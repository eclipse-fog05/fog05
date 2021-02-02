pipeline {
  agent {
    kubernetes {
      label 'my-agent-pod'
      yaml """
apiVersion: v1
kind: Pod
spec:
  containers:
  - name: ubu20
    image: fog05/ubuntu-build:focal
    command:
    - cat
    tty: true
    resources:
      limits:
        memory: "2Gi"
        cpu: "1"
      requests:
        memory: "2Gi"
        cpu: "1"
"""
    }
  }
  stages {
        stage('install-rust') {
            steps {
                container('ubu20') {
                    sh '''
                        pwd
                        ls
                        id -u
                        curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rust.sh
                        chmod +x /tmp/rust.sh
                        HOME=/home/$(id -u)  /tmp/rust.sh --default-toolchain nightly -y
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo
                        cargo install cargo-deb
                    '''
                }
            }
        }

        stage('check') {
            steps {
                container('ubu20') {
                    sh '''
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo
                        cargo check
                        cargo fmt -- --check
                        cargo clippy --all
                    '''
                }
            }
        }


        stage('build') {
            steps {
                container('ubu20') {
                    sh '''
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo
                        cargo build --release --all-targets
                        cargo deb -p fog05-agent --no-build
                        cargo deb -p fog05-fosctl --no-build
                    '''
                }
            }
        }

    }
}