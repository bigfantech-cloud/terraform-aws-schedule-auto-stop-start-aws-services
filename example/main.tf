module "schedule_rds_ecs_stop_start_cron" {
  source = "bigfantech-cloud/schedule-auto-stop-start-aws-services/aws"
  # version      = "a.b.c" find the latest version from https://registry.terraform.io/modules/bigfantech-cloud/ecs-terraform-cloud-agent/aws/latest

  project_name            = "abc"
  rds_stop_cron           = "cron(0 18 ? * MON-FRI *)"
  rds_start_cron          = "cron(0 2 ? * MON-FRI *)"
  schedule_rds_stop_start = true
  schedule_ecs_stop_start = true
  rds_cluster_arn_parameter_names_list = [
    "/an/ssm/parameter/name",
    "/another/ssm/parameter/name",
  ]
  ecs_cluster_name_to_service_names_map = {
    acluster_name = [
      aservice_name,
      another_service_name
    ]
    another_cluster_name = [
      aservice_name,
      another_service_name
    ]
  }
}
