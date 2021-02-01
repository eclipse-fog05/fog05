pipeline {
    agent any
    stages {
        stage('build') {
            steps {
                sh
                "
                env
                pwd
                uname -a
                "
            }
        }
    }
}