variable "schedule_rds_stop_start" {
  description = "Whether to schedule RDS Stop/Start"
  type        = bool
  default     = false
}

variable "schedule_ecs_stop_start" {
  description = "Whether to schedule ECS tasks Stop/Start"
  type        = bool
  default     = false
}

variable "stop_cron" {
  description = "CRON expression to schedule STOP"
  type        = string
  default     = null
}

variable "start_cron" {
  description = "CRON expression for schedule START"
  type        = string
  default     = null
}

variable "rds_cluster_arn_parameter_names_list" {
  description = "List of RDS cluster ARN SSM parameter names to schedule stop/start"
  type        = list(string)
  default     = []
}

variable "rds_instance_arn_parameter_names_list" {
  description = "List of RDS instance ARN SSM parameter names to schedule stop/start"
  type        = list(string)
  default     = []
}

variable "ecs_cluster_name_to_service_names_map" {
  description = "Map of ECS cluster name to list of ECS Service names to schedule stop/start"
  type        = map(any)
  default     = {}
}
