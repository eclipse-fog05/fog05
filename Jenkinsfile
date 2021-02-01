pipeline {
    agent any
    stages {

        stage('build') {
            steps {
                sh
                '''
                    cargo check
                    cargo fmt -- --check
                    cargo clippy --all
                    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs -o /tmp/rust.sh
                    chmod +x /tmp/rust.sh
                    /tmp/rust.sh --default-toolchain nightly -y
                    cargo install cargo-deb
                    cargo build --release --all-targets
                    cargo deb -p fog05-agent --no-build
                    cargo deb -p fog05-fosctl --no-build
                '''
            }
        }

    }
}