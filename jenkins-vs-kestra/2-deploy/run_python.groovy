pipeline {
    agent { docker { image 'python:3.9.0' } }
    
    stages {
        stage('checkout') {
            steps {
                git(
                    url: 'https://github.com/wrussell1999/kestra-examples.git',
                    branch: 'main'
                ) 
            }
        }
        stage('dependencies') {
            steps {
                sh 'python3 -m venv .venv'
            }
        }
        stage('tests') {
            steps {
                sh '. .venv/bin/activate && python jenkins-vs-kestra/2-deploy/example.py'
            }
        }
    }
}
