# uploads/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
import io 
import pandas as pd
from django.conf import settings

from .forms import UploadFileForm
from .serializers import EntitiesSerializer, HistorySerializer, SprintsSerializer, Entities
# from .models import UploadedFile


def upload_files(request):
    if request.method == 'POST':
        # print('1111111111')
        files = request.FILES.getlist('file')
        
        if len(files) == 3:
            for file in files:
                file_name = file.name.lower()  # Get the file name and convert to lowercase
                
                try:
                    # Convert the uploaded file into a BytesIO object
                    file_readed = file.read()
                    file_content = io.BytesIO(file_readed)

                    # Read the CSV file with pandas
                    file_text = file_readed.decode('utf-8').split('\n')

                    i = 0
                    while ';' not in file_text[i]:
                        i += 1

                    df = pd.read_csv(file_content, sep=";", header=0, skiprows=i, encoding='utf-8')
                    # print(df)
                    df.columns = df.columns.str.lower()

                    # Convert the DataFrame to a dictionary
                      # List of dictionaries (row-wise)
                    serializer = None
                    if "entitie" in file_name:
                        # df['entity_id'] = df['entity_id'].apply(lambda x: x if str(x).isdigit() else 0)
                        # df['spent'] = df['spent'].apply(lambda x: x if str(x).isdigit() else 0)
                        # df['estimation'] = df['estimation'].apply(lambda x: x if str(x).isdigit() else 0)
                        # data_dict = df.to_dict(orient='records')
                        settings.DUMMYBASE['entities'] = df
                        # for r in data_dict:
                        #     Entities.objects.create(**r)
                        # print(data_dict[0])
                        # for i in range(len(data_dict)):

                        #     if str(data_dict[i]['spent']).isdigit() == False:
                        #         # print([data_dict[i]['spent']])
                        #         data_dict[i]['spent'] = -1
                        #     if str(data_dict[i]['estimation']).isdigit() == False:
                        #         data_dict[i]['estimation'] = -1
                        #     if str(data_dict[i]['entity_id']).isdigit() == False:
                        #         data_dict[i]['entity_id'] = -1
                        # serializer = EntitiesSerializer(data=data_dict, many=True)
                    elif "history" in file_name:  # Check if 'like' is in the file name
                        # df['entity_id'] = df['entity_id'].apply(lambda x: x if str(x).isdigit() else 0)
                        # data_dict = df.to_dict(orient='records')
                        settings.DUMMYBASE['history'] = df
                        # for i in range(len(data_dict)):
                        #     if str(data_dict[i]['entity_id']).isdigit() == False:
                        #         data_dict[i]['entity_id'] = -1
                        # serializer = HistorySerializer(data=data_dict, many=True)
                    elif "sprint" in file_name:
                        settings.DUMMYBASE['sprints'] = df
                        # data_dict = df.to_dict(orient='records')
                        # serializer = SprintsSerializer(data=data_dict, many=True)
                    else:
                        return JsonResponse({
                            'message': 'File uploaded, but does not contain the necessary word'
                        })
                    # print(file_name)
                    # serializer.is_valid(raise_exception=True)
                    # serializer.save()
                    # return JsonResponse({
                    #     'message': 'CSV file processed successfully',
                    #     'data': data_dict
                    # })
                except Exception as e:
                    return JsonResponse({
                        'error': 'Failed to process the CSV file',
                        'details': str(e)
                    }, status=400)
            # print(settings.DUMMYBASE)
            return redirect('/')
            
        else:
            return JsonResponse({'error': 'bad try'}, status=400)
        
    form = UploadFileForm()
    return render(request, 'uploads/upload_form.html', {'form': form})
    if request.method == 'POST' and request.FILES:
        

        # Save each file to the database
        
            # UploadedFile.objects.create(file=file, description=description)
            print(file)
            pass

        

    

def success(request):
    return render(request, 'uploads/success.html')
