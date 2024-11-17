from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import loader
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import pandas as pd
import numpy as np
import ast
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from django.shortcuts import render, redirect


def parse_all_sprints(entity, history, sprints):
    """
    Распределяет данные `entity`, `history`, и `sprints` по всем спринтам.

    Args:
        entity (pd.DataFrame): Таблица с данными объектов (с колонкой `entity_id`).
        history (pd.DataFrame): Таблица с историей изменений объектов (с колонкой `entity_id`).
        sprints (pd.DataFrame): Таблица спринтов с колонкой `entities` (список `entity_id`) и `sprint_name`.

    Returns:
        dict: Словарь, где ключ — название спринта, а значение — словарь с тремя таблицами:
            - `entity`: Таблица `entity` для спринта.
            - `history`: Таблица `history` для спринта.
            - `sprint_row`: Строка из таблицы `sprints` для спринта.
    """
    sprint_dict = {}
    sprints["entity_ids"] = sprints["entity_ids"].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
    # Итерируемся по строкам таблицы sprints
    for _, sprint_row in sprints.iterrows():
        sprint_name = sprint_row["sprint_name"]
        sprint_entity_ids = sprint_row["entity_ids"]
        
        # Фильтруем entity и history по entity_id из текущего спринта
        filtered_entity = entity[entity["entity_id"].isin(sprint_entity_ids)]
        filtered_history = history[history["entity_id"].isin(sprint_entity_ids)]
        
        # Добавляем в результат
        sprint_dict[sprint_name] = {
            "entity": filtered_entity,
            "history": filtered_history,
            "sprint_row": sprint_row,
        }
    
    return sprint_dict


def process_sprints_from_dict(sprints_dict, selected_sprint_names):
    """
    Обрабатывает данные спринтов из словаря и возвращает отфильтрованные данные.

    Args:
        sprints_dict (dict): Словарь с данными по спринтам.
        selected_sprint_names (list): Названия спринтов для фильтрации.

    Returns:
        dict: Отфильтрованные данные по выбранным спринтам:
            - filtered_sprints: Данные только для выбранных спринтов.
    """
    if isinstance(selected_sprint_names, str):
        selected_sprint_names = [selected_sprint_names]
    
    filtered_sprints = {
        name: {
            "entity": sprints_dict[name]["entity"],
            "history": sprints_dict[name]["history"],
            "sprint_row": sprints_dict[name]["sprint_row"]
        }
        for name in selected_sprint_names if name in sprints_dict
    }

    return {"filtered_sprints": filtered_sprints}


def calculate_metrics_for_active_sprint_with_slider(sprint_name, sprints_dict, days_offset):
    """
    Рассчитывает метрики "К выполнению", "Сделано" и "Снято" для одного активного спринта
    с учетом сдвига дней от даты начала спринта.

    Метрики:
    - "К выполнению" (tasks in "Создано" status).
    - "Сделано" (tasks in "Закрыто" or "Выполнено" status).
    - "Снято" (tasks removed with specific resolutions or statuses).

    Args:
        sprint_name (str): Название активного спринта.
        sprints_dict (dict): Словарь с данными по спринтам.
        days_offset (int): Сдвиг дней от даты начала спринта.

    Returns:
        dict: Словарь с метриками для активного спринта.
    """
    # 2. Извлекаем данные активного спринта
    active_sprint_data = sprints_dict['filtered_sprints'][sprint_name]
    sprint_start_date = pd.to_datetime(active_sprint_data["sprint_row"]["sprint_start_date"])
    sprint_end_date = pd.to_datetime(active_sprint_data["sprint_row"]["sprint_end_date"])
    sprint_tasks = active_sprint_data["entity"]

    # 3. Рассчитываем дату на основе ползунка
    timestamp = sprint_start_date + pd.Timedelta(days=days_offset)
    timestamp = timestamp.replace(hour=23, minute=59, second=59)
    if days_offset == 13:
        timestamp = timestamp.replace(hour=19, minute=0, second=0)

    # 4. Проверяем, входит ли рассчитанная дата в диапазон спринта
    if timestamp > sprint_end_date:
        raise ValueError(f"Указанная дата '{timestamp}' выходит за пределы активного спринта '{sprint_name}'.")

    # 5. Расчет метрики "К выполнению" (to_do)
    to_do_tasks = sprint_tasks[
        (pd.to_datetime(sprint_tasks["update_date"]) <= timestamp) & 
        (sprint_tasks["status"] == "Создано")
    ]
    to_do_metric = to_do_tasks["estimation"].sum() / 3600 if not to_do_tasks.empty else 0

    # 6. Расчет метрики "Сделано" (done)
    done_tasks = sprint_tasks[
        (pd.to_datetime(sprint_tasks["update_date"]) <= timestamp) & 
        (sprint_tasks["status"].isin(["Закрыто", "Выполнено"]))
    ]
    done_metric = done_tasks["estimation"].sum() / 3600 if not done_tasks.empty else 0

    # 7. Расчет метрики "Снято" (removed)
    removed_tasks = sprint_tasks[
        (pd.to_datetime(sprint_tasks["update_date"]) <= timestamp) &
        (
            ((sprint_tasks["status"].isin(["Закрыто", "Выполнено"])) &
             (sprint_tasks["resolution"].isin(["Отклонено", "Отменено инициатором", "Дубликат"]))) |
            ((sprint_tasks["type"] == "Дефект") & (sprint_tasks["status"] == "Отклонен исполнителем"))
        )
    ]
    removed_metric = removed_tasks["estimation"].sum() / 3600 if not removed_tasks.empty else 0

    # 8. Метрика "В работе" (in_progress)
    in_progress_tasks = sprint_tasks[
        (pd.to_datetime(sprint_tasks["update_date"]) >= sprint_start_date) &
        (pd.to_datetime(sprint_tasks["update_date"]) <= timestamp) &
        (~sprint_tasks["status"].isin(["Закрыто", "Выполнено", "Отклонено", "Снято","Отклонен исполнителем","Создано"]))
    ]
    if not in_progress_tasks.empty:
        in_progress_metric = (
            np.where(
                in_progress_tasks["spent"].notna(),
                in_progress_tasks["spent"].fillna(0),
                in_progress_tasks["estimation"].fillna(0)
            ).sum() / 3600
        )

    else:
        in_progress_metric = 0

    start_plus_2_days = sprint_start_date + pd.Timedelta(days=2)

    # Backlog на начало (дата старта + 2 дня)
    backlog_start = sprint_tasks[
        (pd.to_datetime(sprint_tasks["update_date"]) <= start_plus_2_days) &
        (sprint_tasks["status"] == "Создано")
    ]["estimation"].sum() / 3600 if not sprint_tasks.empty else 0

    # Backlog на текущий момент (только созданные задачи спустя 2 дня от старта)
    backlog_current = sprint_tasks[
        (pd.to_datetime(sprint_tasks["update_date"]) > start_plus_2_days) &
        (pd.to_datetime(sprint_tasks["update_date"]) <= timestamp) &
        (sprint_tasks["status"] == "Создано")
    ]["estimation"].sum() / 3600 if not sprint_tasks.empty else 0

    # Разница между Backlog
    backlog_change_metric = round((backlog_current/backlog_start)*100, 1)
    if days_offset==1 or days_offset ==2:
        backlog_change_metric = 0

    # 9. Формируем результат
    result = {
        "sprint_name": sprint_name,
        "metrics": {
            "ready_work": round(to_do_metric, 1),
            "done": round(done_metric, 1),
            "canceled": round(removed_metric, 1),
            "in_work": round(in_progress_metric, 1)
        },
        "backlog_change":backlog_change_metric
         }
    return result


def calculate_percantage_metrics(result):
    metrics = result['metrics']
    total = sum(metrics.values())
    percentages = {key: round((value / total) * 100, 1) for key, value in metrics.items()}
    percentages['backlog_change'] = result['backlog_change']
    return percentages

def analyze_progress_bar(entities,history,sprints,day_offset,choosen_sprints,sprint_name):
    all_sprints = parse_all_sprints(entities,history,sprints)
    sprints_dict = process_sprints_from_dict(all_sprints,choosen_sprints)
    result = calculate_metrics_for_active_sprint_with_slider(sprint_name,sprints_dict,day_offset)
    percentages = calculate_percantage_metrics(result)
    return percentages


def calculate_burn_down_from_history(history_df, sprint_start_date, sprint_end_date):
    """
    Рассчитывает Burn Down Chart на основе истории изменений статусов сущностей.
    
    Args:
        history_df (pd.DataFrame): История изменений с колонками 'entity_id', 'status', 'history_date'.
        sprint_start_date (datetime): Дата начала спринта.
        sprint_end_date (datetime): Дата окончания спринта.
        
    Returns:
        dict: Данные для Burn Down Chart в виде словаря с датами и значениями.
    """
    # Преобразуем даты в формате истории
    history_df['history_date'] = pd.to_datetime(history_df['history_date'])
    
    # Создаем диапазон дат спринта
    dates_range = pd.date_range(start=sprint_start_date, end=sprint_end_date, freq='D')
    burn_down_data = pd.DataFrame(dates_range, columns=['date'])
    
    # Рассчитываем метрики для каждой даты
    for idx, current_date in enumerate(burn_down_data['date']):
        # Учитываем все изменения до текущей даты включительно
        history_up_to_date = history_df[history_df['history_date'] <= current_date]
        
        # Количество открытых задач (статусы, не содержащие закрывающих подстрок)
        open_tasks = len(
            history_up_to_date[~history_up_to_date['history_change'].str.contains(
                'closed|rejectedByThePerformer|done', case=False, na=False
            )]['entity_id'].unique()
        )
        
        # Количество закрытых задач (статусы, содержащие закрывающие подстроки)
        closed_tasks = len(
            history_up_to_date[history_up_to_date['history_change'].str.contains(
                'closed|rejectedByThePerformer|done', case=False, na=False
            )]['entity_id'].unique()
        )
        
        # Разность между открытыми и закрытыми задачами
        remaining_tasks = open_tasks - closed_tasks
        
        # Заполняем данные для текущей даты
        burn_down_data.loc[idx, 'open_tasks'] = open_tasks
        burn_down_data.loc[idx, 'closed_tasks'] = closed_tasks
        burn_down_data.loc[idx, 'remaining_tasks'] = remaining_tasks
    
    # Рассчитываем максимальное количество оставшихся задач
    max_value_remaining_task = burn_down_data['remaining_tasks'][0]
    descending_score=(max_value_remaining_task / 14)
    # Формируем словарь с данными
    burn_down_dict = {}
    labels = []
    remain_values = []
    ideal_values = []
    for idx, row in burn_down_data.iterrows():
        day_number = idx + 1  # Номер дня (1, 2, 3, ...)
        labels.append(day_number)
        remain_values.append(row['remaining_tasks'])
        ideal_value = max_value_remaining_task - descending_score
        max_value_remaining_task = ideal_value
        if(ideal_value<0):
            ideal_value = 0
        ideal_values.append(ideal_value)
     
    burn_down_dict['label'] = labels
    burn_down_dict['remain_values'] = remain_values
    burn_down_dict['ideal_values'] = ideal_values
    return burn_down_dict


def get_burn_down(entities,history,sprints,name_sprint):
    all_sprints = parse_all_sprints(entities,history,sprints) 
    dict = process_sprints_from_dict(all_sprints, name_sprint)
    sprint_data = list(dict['filtered_sprints'].values())[0]
    history = sprint_data['history']
    start_date = sprint_data['sprint_row']['sprint_start_date']
    end_date = sprint_data['sprint_row']['sprint_end_date']
    burn_down_data = calculate_burn_down_from_history(history, start_date, end_date)
    return burn_down_data



# @api_view(['GET'])
# def test(request):
    # print(res)
    # return ('1')
    # return HttpResponse(str({"message": str(res)}))


def index(request):
    area_data = [
        { "label": "Jan", "y": 10000 },
        { "label": "Feb", "y": 30162 },
        { "label": "Mar", "y": 26263 },
        { "label": "Apr", "y": 18394 },
        { "label": "May", "y": 18287 },
        { "label": "Jun", "y": 28682 },
        { "label": "Jul", "y": 31274 },
        { "label": "Aug", "y": 33259 },
        { "label": "Sep", "y": 25849 },
        { "label": "Oct", "y": 24159 },
        { "label": "Nov", "y": 32651 },
        { "label": "Dec", "y": 31984 }
    ]
    column_data = [
        { "label": "January", "y": 42150 },
        { "label": "February", "y": 53120 },
        { "label": "March", "y": 62510 },
        { "label": "April", "y": 78410 },
        { "label": "May", "y": 98210 },
        { "label": "June", "y": 149840 }
    ]
    pie_data = [
        { "y": 12.21, "name": "Blue", "color": "#007bff" },
        { "y": 15.58, "name": "Red", "color": "#dc3545" },
        { "y": 11.25, "name": "Yellow", "color": "#ffea00" },
        { "y": 8.32, "name": "Green", "color": "#28a745" }
    ]
    return render(request, 'base.html')


def getAllProjects(request):
    sprints = ['Спринт 2024.3.1.NPP Shared Sprint',
               'Спринт 2024.3.2.NPP Shared Sprint',
               'Спринт 2024.3.3.NPP Shared Sprint',
               'Спринт 2024.3.4.NPP Shared Sprint',
               'Спринт 2024.3.5.NPP Shared Sprint',
               'Спринт 2024.3.6.NPP Shared Sprint']
    return render(request, 'Allprojects.html', {'sprints': sprints})


# @renderer_classes((TemplateHTMLRenderer, JSONRenderer))
def get_sprint_bar_data(request, day=None, sprint=None):
    print(day, sprint)
    if settings.DUMMYBASE == {}:
        return render(request, 'projectView.html', {'is_data_exist': False})
    sprints = list(settings.DUMMYBASE['sprints']['sprint_name'].unique())
    choosen_sprints = settings.DUMMYBASE['sprints']['sprint_name'].unique()
    sprint_name = settings.DUMMYBASE['sprints']['sprint_name'].unique()[0]
    res = analyze_progress_bar(settings.DUMMYBASE['entities'], 
                               settings.DUMMYBASE['history'],
                               settings.DUMMYBASE['sprints'],
                               day,
                               choosen_sprints,
                               sprint_name)
    return JsonResponse({'data': res})


def get_burn(request):
    res = get_burn_down(settings.DUMMYBASE['entities'], 
                        settings.DUMMYBASE['history'],
                        settings.DUMMYBASE['sprints'],
                        settings.SELECTEDSPRINT)

    return JsonResponse({'data': res})


def update_sprint(request):
    settings.SELECTEDSPRINT = request.GET['options']
    return redirect('/')


def getProject(request, pk=None):
    print(settings.DUMMYBASE == {},
          str(settings.DUMMYBASE)[:25])
    if settings.DUMMYBASE == {}:
        return render(request, 'projectView.html', {'is_data_exist': False, 'is_sprint_exist': True})
    sprints = list(settings.DUMMYBASE['sprints']['sprint_name'].unique())
    if settings.SELECTEDSPRINT == "":
        return render(request, 'projectView.html', {'is_data_exist': True,'is_sprint_exist': False, 'sprints': sprints})
    # print(kwargs)
    
    choosen_sprints = settings.DUMMYBASE['sprints']['sprint_name'].unique()
    sprint_name = settings.SELECTEDSPRINT
    res = analyze_progress_bar(settings.DUMMYBASE['entities'], 
                               settings.DUMMYBASE['history'],
                               settings.DUMMYBASE['sprints'],
                               0,
                               choosen_sprints,
                               sprint_name)
    # print(res)
    # const section1Percentage = Number('{{ redy_work }}'); // You can update these values dynamically
    # const section2Percentage = Number('{{ in_work }}');
    # const section3Percentage = Number('{{ done }}');
    # const section4Percentage = Number('{{ canceld }}');
    # {'ready_work': 3.5, 'done': 91.3, 'canceled': 0.9, 'in_work': 3.8, 'backlog_change': 0.5}
    m_d = 0
    l_d = ''
    s = 0 

    for k in res:
        if k == 'backlog_change':
            continue
        s += res[k]
        if res[k] > m_d:
            m_d = res[k]
            l_d = k 
        print(k, res[k])
    print(s, l_d)
    res[l_d] += 100 - s

    resb = get_burn_down(settings.DUMMYBASE['entities'], 
                        settings.DUMMYBASE['history'],
                        settings.DUMMYBASE['sprints'],
                        settings.SELECTEDSPRINT)

    return render(request, 'projectView.html', {'sprints': sprints,
                                                 'ready_work': round(res['ready_work'], 1),
                                                 'done': round(res['done'], 1),
                                                 'canceled': round(res['canceled'], 1),
                                                 'in_work': round(res['in_work'], 1),
                                                 'backlog_change': round(res['backlog_change'], 1),
                                                 'is_data_exist': True,
                                                 'is_sprint_exist': True,
                                                 'q_days': 13,
                                                 'day_numbers': [i for i in range(14)],
                                                 'burn': resb})