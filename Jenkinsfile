   pipeline {
     agent any

     triggers {
       githubpush()
     }

     stages {
       stage('Checkout') {
         steps {
           // Checkout the repository
           checkout scm
         }
         
       }
       
     }
     
  }
