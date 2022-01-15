output "region" {
  value = var.region
}

# TODO make cluster specific variable names/outputs
output "vpc_id" {
  value = module.apn1_vpc.vpc_id
}

output "vpc_cidr_block" {
  value = module.apn1_vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  value = module.apn1_vpc.public_subnet_ids
}

output "public_route_table_ids" {
  value = module.apn1_vpc.public_route_table_ids
}

output "private_subnet_ids" {
  value = module.apn1_vpc.private_subnet_ids
}

output "private_route_table_ids" {
  value = module.apn1_vpc.private_route_table_ids
}

output "default_security_group_id" {
  value = module.apn1_vpc.default_security_group_id
}

output "nat_gateway_ids" {
  value = module.apn1_vpc.nat_gateway_ids
}

output "availability_zones" {
  value = var.azs
}

output "kops_s3_bucket_name" {
  value = module.kops_resources.kops_s3_bucket_name
}

output "kops_hosted_zone_name_severs" {
  value = module.kops_resources.kops_hosted_zone_name_severs
}

#output "k8s_security_group_id" {
#  value = module.apn1_kops_resources.k8s_security_group_id
#}

output "k8s_non_masquerade_cidr" {
  value = var.k8s_non_masquerade_cidr
}

output "cluster_name" {
  value = local.cluster_name
}