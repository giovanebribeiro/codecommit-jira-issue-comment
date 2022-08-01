/* 
 * Lista de variáveis da infraestrutura. Para setar os valores de acordo com o
 * workspace, acesse o arquivo tfvars e edite as variáveis desejadas.
 * https://www.terraform.io/docs/backends/types/s3.html 
 */

variable "aws_bucket_tfstates" {
    type = string
    description = "Nome do bucket que vai armazenar os arquivos tfstate"
}

variable "region" {
	type = string
	description = "Região da AWS"
	default = "us-east-1"
}

variable "aws_profile" {
    type = string
    description = "Profile da AWS"
    default = "default"
}