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
                sh '. .venv/bin/activate && pip install pytest'
            }
        }
        stage('tests') {
            steps {
                sh '. .venv/bin/activate && pytest demos/jenkins-vs-kestra/1-tests'
            }
        }
    }
}
