# BigFantech-Cloud

We automate your infrastructure.
You will have full control of your infrastructure, including Infrastructure as Code (IaC).

To hire, email: `bigfantech@yahoo.com`

# Purpose of this code

> Terraform module

To schedule auto Stop Start CRON for different AWS services using Lambda function.

List of AWS services can be managed:

- ECS Services
- RDS Cluster
- RDS instance

> When scheduling RDS and ECS Stop/Start, ECS will start once RDS is in `available` status to avoid connection failure between applicaiton running in ECS and DB.
> if the applicaiton is running in ECS and accessing RDS DB, it is recommended to Schedule both RDS & ECS

## Required Providers

| Name                | Description |
| ------------------- | ----------- |
| aws (hashicorp/aws) | >= 4.47     |

## Variables

### Required Variables

| Name           | Description                       | Type   | Default |
| -------------- | --------------------------------- | ------ | ------- |
| `project_name` |                                   | string |         |
| `stop_cron`    | CRON expression to schedule STOP  | string |         |
| `start_cron`   | CRON expression to schedule START | string |         |

### Optional Variables

| Name                                    | Description                                                                 | Type         | Default |
| --------------------------------------- | --------------------------------------------------------------------------- | ------------ | ------- |
| `environment`                           |                                                                             |              |         |
| `schedule_rds_stop_start`               | Whether to schedule RDS Stop/Start                                          | bool         | false   |
| `schedule_ecs_stop_start`               | Whether to schedule ECS tasks Stop/Start                                    | bool         | false   |
| `rds_cluster_arn_parameter_names_list`  | List of RDS cluster ARN SSM parameter names to schedule stop/start          | list(string) | []      |
| `rds_instance_arn_parameter_names_list` | List of RDS instance ARN SSM parameter names to schedule stop/start         | list(string) | []      |
| `ecs_cluster_name_to_service_names_map` | Map of ECS cluster name to list of ECS Service names to schedule stop/start | map(any)     | {}      |

### Example config

> Check the `example` folder in this repo
