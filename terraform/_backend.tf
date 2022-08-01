terraform {
	
   /* 
	* CONFIGURACAO DO BACKEND PARA O TERRAFORM 
	* https://www.terraform.io/docs/backends/types/s3.html 
	*/
	backend "s3" {
		bucket = var.aws_bucket_tfstates
		key    = "codecommit-jira-integration/terraform.tfstate"
		region = var.region
	}

}