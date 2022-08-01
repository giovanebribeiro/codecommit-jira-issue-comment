/*
 * Configurações referentes aos providers utilizados pelo terraform
 */
 
# Utilizado para se determinar o ID da conta
data "aws_caller_identity" "current" {}

##### Configurações do Provider ######
provider "aws" {
    region                      = var.region
    shared_credentials_files    = [ "$HOME/.aws/credentials" ]
    profile                     = var.aws_profile
}