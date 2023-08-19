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

# Select RDS to perform Start action based on ARN in given SSM parameters
def find_rds_to_start():
    global start_rds_clusters_config
    global start_rds_instances_config
    start_rds_clusters_config    = []
    start_rds_instances_config   = []

# CLUSTER
    if  len(rds_cluster_arn_parameter_names_list) > 0:   
        cluster_arn_parameters = client_ssm.get_parameters(
            Names=rds_cluster_arn_parameter_names_list,
            WithDecryption=True
        )
        start_rds_clusters_arn=[ i['Value'] for i in cluster_arn_parameters['Parameters']]
    
        for arn in start_rds_clusters_arn:
            start_rds_clusters_config.extend([ i for i in all_rds_clusters_config if arn == i['DBClusterArn'] ])

# INSTANCE
    if len(rds_instance_arn_parameter_names_list) > 0:
        instance_arn_parameters = client_ssm.get_parameters(
            Names=rds_instance_arn_parameter_names_list,
            WithDecryption=True
        )
        start_rds_instances_arn=[ i['Value'] for i in instance_arn_parameters['Parameters']]

        for arn in start_rds_instances_arn:
            start_rds_instances_config.extend([ i for i in all_rds_instances_config if arn == i['DBInstanceArn'] ])
    

def start_rds():
    print('Executing: start RDS...')
# CLUSTER
    for i in start_rds_clusters_config:
        if i['Status'] == 'stopped':
            client_rds.start_db_cluster(
                DBClusterIdentifier=i['DBClusterIdentifier']
            )
            print('Starting DB Cluster "{0}"'.format(i['DBClusterIdentifier']))
        elif i['Status'] == 'available':
            print('DB Cluster "{0}" is already in available state'.format(i['DBClusterIdentifier']))
        elif i['Status'] == 'starting':
            print('DB Cluster "{0}" is already in starting state'.format(i['DBClusterIdentifier']))
        elif i['Status'] == 'stopping':
            print('DB Cluster "{0}" is in stopping state. Try again once the cluster has stopped'.format(i['DBClusterIdentifier']))

# INSTANCE
    for i in start_rds_instances_config:
        if i['DBInstanceStatus'] == 'stopped':
            client_rds.start_db_instance(
                DBInstanceIdentifier=i['DBInstanceIdentifier']
            )
            print('Starting DB Instance "{0}"'.format(i['DBInstanceIdentifier']))
        elif i['DBInstanceStatus'] == 'available':
            print('DB Instance "{0}" is already in available state'.format(i['DBInstanceIdentifier']))
        elif i['DBInstanceStatus'] == 'starting':
            print('DB Instance "{0}" is already in starting state'.format(i['DBInstanceIdentifier']))
        elif i['DBInstanceStatus'] == 'stopping':
            print('DB Instance "{0}" is in stopping state. Try again once the cluster has stopped'.format(i['DBInstanceIdentifier']))

# Verifying if all the RDS are in `available` state
# Performed before starting ECS to avoid Applicaiton connection to DB failure
def rds_status_check():
    global all_rds_running
    all_rds_running = False

    for t in [300, 300, 120, 120, 120]:
        if not all_rds_running:
            print('Wating grace period of ' + str(t)+'sec before checking RDS status...')
            time.sleep(t)
            all_rds_status=[
                i['Status'] for i in start_rds_clusters_config if i['Status'] != 'available']+[
                i['DBInstanceStatus'] for i in start_rds_instances_config if i['DBInstanceStatus'] != 'available']
        if len(all_rds_status) == 0:
            print('All RDS are on available status..')  
            all_rds_running = True 
        else:
            print('Not all RDS are on available status yet..')

#---
# ECS
#---

def start_ecs_task():
    print('Executing: start ECS task...')
    for cluster, services in ecs_cluster_name_to_service_names_dict.items():
        for service in services:
            current_service_task_desired_count = client_ecs.describe_services(
                    cluster=cluster,
                    services=[
                        service
                    ],
                )['services'][0]['desiredCount']
            
            task_count_before_stopping = client_ssm.get_parameter(
                Name= '/lamdbda-function/scheduled-stop-start/ecs/TaskCountBeforeStopping/' + service,
            )['Parameters']['Value':]

            if current_service_task_desired_count != task_count_before_stopping:
                print('Current Service desiredCount is: {0}. Starting ECS tasks: setting {1} Service desiredCount to count recorded before stopping the service= {2} ...'.format(current_service_task_desired_count, service, task_count_before_stopping))
                client_ecs.update_service (
                    cluster = cluster, 
                    service = service,
                    desiredCount = task_count_before_stopping
                )
            else:
                print('ECS ' + service + ' Service tasks are already running required desiredCount, no action done...')

def lambda_handler(event, context):
    if schedule_rds_stop_start:
        find_rds_to_start()
        start_rds()
    
    if schedule_ecs_stop_start:
        if schedule_rds_stop_start:
            rds_status_check()
            if all_rds_running:
                start_ecs_task()
            else:
                print('SKIPPED: START ECS TASK. NOT ALL RDS ARE IN AVAILABLE STATE...')
        else:
            start_ecs_task()