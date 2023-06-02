#-----
#IAM FOR LAMBDA FUNCTION - RDS START/STOP
#-----

data "aws_iam_policy_document" "start_stop_permissions" {

  statement {
    effect = "Allow"

    actions = [
      "rds:DescribeDBClusters",
      "rds:DescribeGlobalClusters",
      "rds:StartDBCluster",
      "rds:StopDBCluster",
      "rds:DescribeDBClusterEndpoints",
      "rds:DescribeDBClusterParameters",
      "rds:DescribeDBClusterParameterGroups",
      "rds:DescribeDBInstances",
      "rds:StopDBInstance",
      "rds:StartDBInstance",
      "rds:DescribeReservedDBInstancesOfferings",
      "rds:DescribeReservedDBInstances",
      "rds:DescribeDBEngineVersions",
      "rds:DescribePendingMaintenanceActions",
      "rds:DescribeValidDBInstanceModifications",
      "rds:DescribeSourceRegions",
      "rds:ListTagsForResource",
      "rds:DescribeDBLogFiles",
      "rds:DescribeOptionGroups",

      "ssm:Describe*",
      "ssm:Get*",
      "ssm:List*",
      "ssm:PutParameter",

      "ecs:List*",
      "ecs:Describe*",
      "ecs:UpdateService",

      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "*"
    ]
  }
}

resource "aws_iam_role" "start_stop_role" {
  name = "${module.this.id}-RDSStartStopLambdaRole"

  assume_role_policy = jsonencode({
    Version = "2008-10-17"
    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "lambda.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      },
    ]
  })
}


resource "aws_iam_role_policy" "start_stop_policy" {

  name   = "${module.this.id}-RDSStartStopLambdaPolicy"
  role   = aws_iam_role.start_stop_role.id
  policy = data.aws_iam_policy_document.start_stop_permissions.json
}
