# uploads/models.py
from django.db import models


class Entities(models.Model):
    '''
    entity_id;area;type;status;state;priority;ticket_number;name;create_date;created_by;update_date;updated_by;parent_ticket_id;assignee;owner;due_date;rank;estimation;spent;workgroup;resolution
    '''
    entity_id = models.IntegerField(blank=True, null=True)
    area = models.TextField(blank=True, null=True)
    type = models.TextField(blank=True, null=True)
    status = models.TextField(blank=True, null=True)
    state = models.TextField(blank=True, null=True)
    priority = models.TextField(blank=True, null=True)
    ticket_number = models.TextField(blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    create_date = models.TextField(blank=True, null=True)
    created_by = models.TextField(blank=True, null=True)
    update_date = models.TextField(blank=True, null=True)
    updated_by = models.TextField(blank=True, null=True)
    parent_ticket_id = models.TextField(blank=True, null=True)
    assignee = models.TextField(blank=True, null=True)
    owner = models.TextField(blank=True, null=True)
    due_date = models.TextField(blank=True, null=True)
    rank = models.TextField(blank=True, null=True)
    estimation = models.IntegerField(blank=True, null=True)
    spent = models.IntegerField(blank=True, null=True)
    workgroup = models.TextField(blank=True, null=True)
    resolution = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'entities'


class Sprints(models.Model):
    '''
    sprint_name;sprint_status;sprint_start_date;sprint_end_date;entity_ids
    '''
    sprint_name = models.TextField(blank=True, null=True)
    sprint_status = models.TextField(blank=True, null=True)
    sprint_start_date = models.TextField(blank=True, null=True)
    sprint_end_date = models.TextField(blank=True, null=True)
    ticket_number = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'sprint'


class History(models.Model):
    '''
    entity_id;history_property_name;history_date;history_version;history_change_type;history_change;Столбец1;
    '''
    entity_id = models.IntegerField(blank=True, null=True)
    history_property_name = models.TextField(blank=True, null=True)
    history_date = models.TextField(blank=True, null=True)
    history_version = models.TextField(blank=True, null=True)
    history_change_type = models.TextField(blank=True, null=True)
    history_change = models.TextField(blank=True, null=True)
    class Meta:
        db_table = 'history'
