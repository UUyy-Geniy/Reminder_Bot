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
                        bat 'powershell Remove-Item Reminder_Bot_job/.git* -Recurse -Force'
                        bat 'ls'
                    }
                }
                echo '===============git repo downloaded==================='
            }
        }
        stage('Getting env variables') {
            steps {
                echo '===============getting env variables==================='
                withCredentials([file(credentialsId: 'ENV', variable: 'ENV')]) {
                    script {
                        if (isUnix()) {
                            sh 'cp $ENV ./.env'
                        } else {
                            bat 'powershell Copy-Item %ENV% -Destination ./.env'
                        }
                    }
                }
            }
        }
    }
    post {
        success {
            echo '===============run docker==================='
                script {
                    if (isUnix()) {
                        sh 'docker build -t reminder_bot .'
                        sh 'docker run --name reminder_botdocker_job -d --rm reminder_bot'
                    } else {
                        bat 'docker build -t reminder_bot .'
                        bat 'docker run --name reminder_botdocker_job -d --rm reminder_bot'
                    }
                }
                echo '===============docker container is running successfully==================='
            }
        }
    }