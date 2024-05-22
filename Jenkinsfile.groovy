pipeline {
    agent any

    stages {
        stage('Build') {
            steps {
                echo 'Building...'
            }
        }
//         stage('Stop old container') {
//             steps {
//                 echo '===============stopping old container==================='
//                 script {
//                     if (isUnix()) {
//                         sh 'docker stop rpi_bot || true'
//                     } else {
//                         bat 'docker stop rpi_bot || true'
//                     }
//                 }
//                 echo '===============old container successfully stopped==================='
//             }
//         }
        stage('Download git repo') {
            steps {
                echo '===============downloading git repo==================='
                script {
                    if (isUnix()) {
                        sh 'rm -rf RPI_Bot'
                        sh 'git clone --depth=1 https://github.com/UUyy-Geniy/Reminder_Bot.git'
                        sh 'rm -rf RPI_Bot/.git*'
                        sh 'ls'
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
                        } else {
                            bat 'powershell Copy-Item %ENV% -Destination ./Reminder_Bot/.env'
                            bat 'powershell Copy-Item %CREDS% -Destination ./Reminder_Bot/credentials_3.json'
                            bat 'powershell Copy-Item %TOKEN% -Destination ./Reminder_Bot/token_3.json'
                            bat 'icacls ./Reminder_Bot/token_3.json /grant everyone:F'
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
                        sh 'cd Reminder_Bot && docker-compose up --build'
//                         sh 'docker run --name reminder_botdocker_job -d --rm reminder_bot'
                    } else {
                        bat 'cd Reminder_Bot && docker-compose up --build'
//                         bat 'docker run --name reminder_botdocker_job -d --rm reminder_bot'
                    }
                }
                echo '===============docker container is running successfully==================='
            }
        }
    }