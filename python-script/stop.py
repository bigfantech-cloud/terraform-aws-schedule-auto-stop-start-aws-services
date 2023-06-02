import boto3
import os
import sys
import time
from datetime import datetime, timezone
from time import gmtime, strftime

client_rds                              = boto3.client('rds')
client_ssm                              = boto3.client('ssm')
client_ecs                              = boto3.client('ecs')
all_rds_clusters_config                 = client_rds.describe_db_clusters()['DBClusters']
all_rds_instances_config                = client_rds.describe_db_instances()['DBInstances']
schedule_rds_stop_start                 = os.environ['schedule_rds_stop_start'] == "true"
schedule_ecs_stop_start                 = os.environ['schedule_ecs_stop_start'] == "true"
rds_cluster_arn_parameter_names_list    = os.environ['rds_cluster_arn_parameter_names_list']
rds_instance_arn_parameter_names_list   = os.environ['rds_instance_arn_parameter_names_list']
ecs_cluster_name_to_service_names_dict  = os.environ['ecs_cluster_name_to_service_names_dict']

#---
# RDS
#---

# Select RDS to perform Stop action based on ARN in given SSM parameters
def find_rds_to_stop():
    global stop_rds_clusters_config
    global stop_rds_instances_config
    stop_rds_clusters_config    = []
    stop_rds_instances_config   = []

# CLUSTER
    if  len(rds_cluster_arn_parameter_names_list) > 0:   
        cluster_arn_parameters = client_ssm.get_parameters(
            Names=rds_cluster_arn_parameter_names_list,
            WithDecryption=True
        )
        stop_rds_clusters_arn=[ i['Value'] for i in cluster_arn_parameters['Parameters']]
    
        for arn in stop_rds_clusters_arn:
            stop_rds_clusters_config.extend([ i for i in all_rds_clusters_config if arn == i['DBClusterArn'] ])

# INSTANCE
    if len(rds_instance_arn_parameter_names_list) > 0:
        instance_arn_parameters = client_ssm.get_parameters(
            Names=rds_instance_arn_parameter_names_list,
            WithDecryption=True
        )
        stop_rds_instances_arn=[ i['Value'] for i in instance_arn_parameters['Parameters']]

        for arn in stop_rds_instances_arn:
            stop_rds_instances_config.extend([ i for i in all_rds_instances_config if arn == i['DBInstanceArn'] ])

def stop_rds():
    print('Executing: stop RDS...')
# CLUSTER
    for i in stop_rds_clusters_config:
        if i['Status'] == 'available':
            client_rds.stop_db_cluster(
                DBClusterIdentifier=i['DBClusterIdentifier']
            )
            print('Stopping DB Cluster "{0}"'.format(i['DBClusterIdentifier']))
        elif i['Status'] == 'stopped':
            print('DB Cluster "{0}" is already stopped'.format(i['DBClusterIdentifier']))
        elif i['Status'] == 'starting':
            print('DB Cluster "{0}" is in starting state. Try again once the cluster is available'.format(i['DBClusterIdentifier']))
        elif i['Status'] == 'stopping':
            print('DB Cluster "{0}" is already in stopping state.'.format(i['DBClusterIdentifier']))

# INSTANCE 
    for i in stop_rds_instances_config:
        if i['DBInstanceStatus'] == 'available':
            client_rds.stop_db_instance(
                DBInstanceIdentifier=i['DBInstanceIdentifier']
            )
            print('Stopping DB Instance "{0}"'.format(i['DBInstanceIdentifier']))
        elif i['DBInstanceStatus'] == 'stopped':
            print('DB Instance "{0}" is already stopped'.format(i['DBInstanceIdentifier']))
        elif i['DBInstanceStatus'] == 'starting':
            print('DB Instance "{0}" is in starting state. Try again once the cluster is available'.format(i['DBInstanceIdentifier']))
        elif i['DBInstanceStatus'] == 'stopping':
            print('DB Instance "{0}" is already in stopping state.'.format(i['DBInstanceIdentifier']))

#---
# ECS
#---

def stop_ecs_task():
    print('Executing: stop ECS task...')
    for cluster, services in ecs_cluster_name_to_service_names_dict.items():
        for service in services:
            current_service_task_desired_count = client_ecs.describe_services(
                    cluster=cluster,
                    services=[
                        service
                    ],
                )['services'][0]['desiredCount']
            ssm_parameter_exists = len(client_ssm.get_parameters(
                Names=[
                        '/lamdbda-function/scheduled-stop-start/ecs/TaskCountBeforeStopping/' + service,
                    ],
            )['Parameters']) > 0

            if ssm_parameter_exists:
                print('ServiceTaskCount SSM Parameter exists, updating the value...')
                client_ssm.put_parameter(
                    Name='/lamdbda-function/scheduled-stop-start/ecs/TaskCountBeforeStopping/' + service,
                    Value=current_service_task_desired_count,
                    Type='String',
                    Overwrite=True
                )
            else:
                print('ServiceTaskCount SSM Parameter does not exist, creating SSM Parameter...')
                client_ssm.put_parameter(
                    Name='/lamdbda-function/scheduled-stop-start/ecs/TaskCountBeforeStopping/' + service,
                    Value=current_service_task_desired_count,
                    Type='String',
                )

            if current_service_task_desired_count == 0:
                print('ECS ' + service + ' Service desiredCount is already = 0, no action required...')
            else:
                print('Stopping ECS tasks: setting ' + service + ' Service desiredCount = 0 ...')
                client_ecs.update_service (
                    cluster = cluster, 
                    service = service,
                    desiredCount = 0
                )

def lambda_handler(event, context):
    if schedule_ecs_stop_start:
        stop_ecs_task()
        
    if schedule_rds_stop_start:
        if schedule_ecs_stop_start:
            print('Waiting for grace 60sec after stopping ECS tasks...')
            time.sleep(60)
            stop_rds()