locals {
  stop_function_name  = "${module.this.id}-aws-services-scheduled-stop"
  start_function_name = "${module.this.id}-aws-services-scheduled-start"
}
#-----
# LAMBDA: STOP
#-----

data "archive_file" "stop" {
  type        = "zip"
  source_file = "${path.module}/python-script/stop.py"
  output_path = "${path.module}/python-script/stop.zip"
}

resource "aws_lambda_function" "scheduled_stop" {
  function_name = local.stop_function_name
  description   = "Stop - Scheduled AWS services Stop/Start"
  architectures = ["arm64"]
  memory_size   = 128
  package_type  = "Zip"
  filename      = data.archive_file.stop.output_path
  role          = aws_iam_role.start_stop_role.arn
  handler       = "stop.lambda_handler"
  runtime       = "python3.9"

  environment {
    variables = {
      schedule_rds_stop_start                = var.schedule_rds_stop_start
      schedule_ecs_stop_start                = var.schedule_ecs_stop_start
      rds_cluster_arn_parameter_names_list   = jsonencode(var.cluster_arn_parameter_names_list)
      rds_instance_arn_parameter_names_list  = jsonencode(var.instance_arn_parameter_names_list)
      ecs_cluster_name_to_service_names_dict = jsonencode(var.ecs_cluster_name_to_service_names_map)
    }
  }

  tags = module.this.tags
}

resource "aws_lambda_permission" "scheduled_stop" {
  statement_id  = "AllowEventBridgeToInvokeLambdaFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduled_stop.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_stop.arn
}

#-----
# LAMBDA: START
#-----

data "archive_file" "start" {
  type        = "zip"
  source_file = "${path.module}/python-script/start.py"
  output_path = "${path.module}/python-script/start.zip"
}

resource "aws_lambda_function" "scheduled_start" {
  function_name = local.start_function_name
  description   = "Start - Scheduled AWS services Stop/Start"
  filename      = data.archive_file.start.output_path
  architectures = ["arm64"]
  role          = aws_iam_role.start_stop_role.arn
  handler       = "start.lambda_handler"
  runtime       = "python3.9"

  environment {
    variables = {
      schedule_rds_stop_start                = var.schedule_rds_stop_start
      schedule_ecs_stop_start                = var.schedule_ecs_stop_start
      rds_cluster_arn_parameter_names_list   = jsonencode(var.cluster_arn_parameter_names_list)
      rds_instance_arn_parameter_names_list  = jsonencode(var.instance_arn_parameter_names_list)
      ecs_cluster_name_to_service_names_dict = jsonencode(var.ecs_cluster_name_to_service_names_map)
    }
  }

  tags = module.this.tags
}

resource "aws_lambda_permission" "scheduled_start" {
  statement_id  = "AllowEventBridgeToInvokeLambdaFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.scheduled_start.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.scheduled_start.arn
}

#-----
#EVENT BRIDGE RULE: STOP
#-----

resource "aws_cloudwatch_event_rule" "scheduled_stop" {
  name                = local.stop_function_name
  description         = "Stop - Scheduled AWS services Stop/Start"
  schedule_expression = var.stop_cron

  tags = module.this.tags
}

resource "aws_cloudwatch_event_target" "stop_lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled_stop.name
  target_id = local.stop_function_name
  arn       = aws_lambda_function.scheduled_stop.arn
}

#-----
#EVENT BRIDGE RULE: START
#-----

resource "aws_cloudwatch_event_rule" "scheduled_start" {
  name                = local.start_function_name
  description         = "Start - Scheduled AWS services Stop/Start"
  schedule_expression = var.start_cron

  tags = module.this.tags
}

resource "aws_cloudwatch_event_target" "start_lambda" {
  rule      = aws_cloudwatch_event_rule.scheduled_start.name
  target_id = local.start_function_name
  arn       = aws_lambda_function.scheduled_start.arn
}
