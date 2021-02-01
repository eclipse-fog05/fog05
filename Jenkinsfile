pipeline {
    agent any
    stages {
        stage('install-rust') {
            steps {
                sh 'curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rust.sh'
                sh 'chmod +x /tmp/rust.sh'
                sh '/tmp/rust.sh --default-toolchain nightly -y'
                sh 'cargo install cargo-deb'

            }
        }

        stage('check') {
            steps {
                sh 'cargo check'
                sh 'cargo fmt -- --check'
                sh 'cargo clippy --all'

            }
        }


        stage('build') {
            steps {
                sh 'cargo install cargo-deb'
                sh 'cargo build --release --all-targets'
                sh 'cargo deb -p fog05-agent --no-build'
                sh 'cargo deb -p fog05-fosctl --no-build'
            }
        }

    }
}