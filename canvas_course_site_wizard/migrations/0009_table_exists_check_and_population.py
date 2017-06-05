# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db import connection

CANVAS_SCHOOL_TEMPLATE_DATA = [
    (3110, 'colgsas', 1, 0),
    (3113, 'colgsas', 1, 1),
    (3114, 'colgsas', 1, 1),
    (3833, 'hsph', 0, 0),
    (3817, 'gse', 0, 0),
    (3111, 'gse', 1, 1),
    (3112, 'hds', 1, 1),
    (28, 'hsph', 0, 0),
]


# Loads the CANVAS_SCHOOL_DATA list information into the canvas_school_template_database
def load_school_template_data(apps, schema_editor):
    CanvasSchoolTemplate = apps.get_model('canvas_course_site_wizard', 'CanvasSchoolTemplate')
    fields = ('template_id', 'school_id', 'is_default', 'include_course_info')

    for canvas_school_template in CANVAS_SCHOOL_TEMPLATE_DATA:
        CanvasSchoolTemplate.objects.get_or_create(**dict(zip(fields, canvas_school_template)))


# Will create a table in the database if it currently does not exist and load any data into the newly created table.
def table_exists_or_create(apps, schema_editor):

    if not db_table_exists('bulk_canvas_course_crtn_job'):
        migrations.CreateModel(
            name='BulkCanvasCourseCreationJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('school_id', models.CharField(max_length=10)),
                ('sis_term_id', models.IntegerField()),
                ('sis_department_id', models.IntegerField(null=True, blank=True)),
                ('sis_course_group_id', models.IntegerField(null=True, blank=True)),
                ('template_canvas_course_id', models.IntegerField(null=True, blank=True)),
                ('status', models.CharField(default=b'setup', max_length=25,
                                            choices=[(b'setup', b'setup'), (b'pending', b'pending'),
                                                     (b'finalizing', b'finalizing'),
                                                     (b'notification_successful', b'notification_successful'),
                                                     (b'notification_failed', b'notification_failed')])),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by_user_id', models.CharField(max_length=20)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'bulk_canvas_course_crtn_job',
            },
        )

    if not db_table_exists('canvas_school_template'):
        migrations.CreateModel(
            name='CanvasSchoolTemplate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('template_id', models.IntegerField()),
                ('school_id', models.CharField(max_length=10, db_index=True)),
                ('is_default', models.BooleanField(default=False)),
                ('include_course_info', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'canvas_school_template',
            }
        )

    if not db_table_exists('canvas_course_generation_job'):
        migrations.CreateModel(
            name='CanvasCourseGenerationJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('canvas_course_id', models.IntegerField(db_index=True, null=True, blank=True)),
                ('sis_course_id', models.CharField(max_length=20, db_index=True)),
                ('content_migration_id', models.IntegerField(null=True, blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
                ('status_url', models.CharField(max_length=200, null=True, blank=True)),
                ('workflow_state', models.CharField(default=b'setup', max_length=20,
                                                    choices=[(b'setup', b'setup'), (b'setup_failed', b'setup_failed'),
                                                             (b'queued', b'queued'), (b'running', b'running'),
                                                             (b'completed', b'completed'), (b'failed', b'failed'),
                                                             (b'pending_finalize', b'pending_finalize'),
                                                             (b'finalized', b'finalized'),
                                                             (b'finalize_failed', b'finalize_failed')])),
                ('created_by_user_id', models.CharField(max_length=20)),
                ('bulk_job_id', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'canvas_course_generation_job',
            },
        )

    load_school_template_data(apps, schema_editor)


# Checks if the given table_name is contained within the database.
def db_table_exists(table_name):
    return table_name in connection.introspection.table_names()


class Migration(migrations.Migration):

    dependencies = [
        ('canvas_course_site_wizard', '0008_auto_20150702_1317'),
    ]

    operations = [
        migrations.RunPython(
            code=table_exists_or_create,
        )
    ]