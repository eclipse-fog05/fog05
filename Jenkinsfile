pipeline {
    agent any
    stages {
        stage('install-rust') {
            steps {
                sh '''
                    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rust.sh
                    chmod +x /tmp/rust.sh
                    /tmp/rust.sh --default-toolchain nightly -y
                    cargo install cargo-deb
                '''
            }
        }

        stage('check') {
            steps {
                sh '''
                    cargo check
                    cargo fmt -- --check
                    cargo clippy --all
                '''
            }
        }


        stage('build') {
            steps {
                sh
                '''
                    cargo build --release --all-targets
                    cargo deb -p fog05-agent --no-build
                    cargo deb -p fog05-fosctl --no-build
                '''
            }
        }

    }
}