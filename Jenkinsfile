pipeline {
    agent {
        kubernetes {
        label 'my-agent-pod'
        yaml """
            apiVersion: v1
            kind: Pod
            spec:
                containers:
                - name: ubuntu
                    image: ubuntu:focal
                    tty: true
            """
        }
  }
    stages {
        stage('install-rust') {
            steps {
                container('ubuntu') {
                    sh 'sudo apt update'
                    sh 'sudo apt install build-essential devscripts debhelper  -y'
                    sh 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rust.sh'
                    sh 'chmod +x /tmp/rust.sh'
                    sh '/tmp/rust.sh --default-toolchain nightly -y'
                    sh 'cargo install cargo-deb'
                    sh 'source $HOME/.cargo/env'
                }
            }
        }

        stage('check') {
            steps {
                container('ubuntu') {
                    sh 'cargo check'
                    sh 'cargo fmt -- --check'
                    sh 'cargo clippy --all'
                }
            }
        }


        stage('build') {
            steps {
                container('ubuntu') {
                    sh 'cargo install cargo-deb'
                    sh 'cargo build --release --all-targets'
                    sh 'cargo deb -p fog05-agent --no-build'
                    sh 'cargo deb -p fog05-fosctl --no-build'
                }
            }
        }

    }
}