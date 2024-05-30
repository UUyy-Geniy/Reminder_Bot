pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building...'
            }
        }
        stage('Download git repo') {
            steps {
                echo '===============downloading git repo==================='
                script {
                    if (isUnix()) {
                        sh 'rm -rf Reminder_Bot'
                        sh 'git clone --depth=1 https://github.com/UUyy-Geniy/Reminder_Bot.git'
                        sh 'rm -rf Reminder_Bot/.git*'
                    } else {
                        bat 'powershell -Command "Get-ChildItem -Path .\\* -Recurse | Remove-Item -Force -Recurse"'
                        bat 'git clone --depth=1 https://github.com/UUyy-Geniy/Reminder_Bot.git'
                        bat 'powershell Remove-Item Reminder_Bot/.git* -Recurse -Force'
                    }
                }
                echo '===============git repo downloaded==================='
            }
        }
        stage('Getting creds and env variables') {
            steps {
                echo '===============getting env variables==================='
                withCredentials([file(credentialsId: 'ENV', variable: 'ENV'), file(credentialsId: 'CREDS', variable: 'CREDS'), file(credentialsId: 'TOKEN', variable: 'TOKEN')]) {
                    script {
                        if (isUnix()) {
                            sh 'cp $ENV ./Reminder_Bot/.env'
                            sh 'cp $REDS ./Reminder_Bot/credentials_4.json'
                            sh 'cp $TOKEN ./Reminder_Bot/token_4.json'
                        } else {
                            bat 'powershell Copy-Item %ENV% -Destination ./Reminder_Bot/.env'
                            bat 'powershell Copy-Item %CREDS% -Destination ./Reminder_Bot/credentials_4.json'
                            bat 'powershell Copy-Item %TOKEN% -Destination ./Reminder_Bot/token_4.json'
                        }
                    }
                }
                echo '===============got creds and env variables==================='
            }
        }
    }
    post {
        success {
            echo '===============run docker==================='
                script {
                    if (isUnix()) {
                        sh 'cd Reminder_Bot && docker-compose up -d --build'
                    } else {
                        bat 'cd Reminder_Bot && docker-compose up -d --build'
                    }
                }
                echo '===============docker container is running successfully==================='
            }
        }
    }