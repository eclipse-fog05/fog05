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
    imagePullPolicy: Always
    command:
    - cat
    tty: true
    resources:
      limits:
        memory: "4Gi"
        cpu: "2"
      requests:
        memory: "4Gi"
        cpu: "2"
"""
    }
  }
  parameters {
    booleanParam(name: 'PUBLISH_ECLIPSE_DOWNLOAD',
        description: 'Publish the resulting artifacts to Eclipse download.',
        defaultValue: false)
  }
  environment {
      LABEL = "nightly"
      DOWNLOAD_DIR="/home/data/httpd/download.eclipse.org/fog05/fog05/${LABEL}"
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

        stage('publish to download.eclipse.org') {
        when { expression { return params.PUBLISH_ECLIPSE_DOWNLOAD }}
        steps {
            // Note: remove existing dir on download.eclipse.org only if it's for a branch
            // (e.g. master that is rebuilt periodically from different commits)
            sshagent ( ['projects-storage.eclipse.org-bot-ssh']) {
            sh '''
                if [[ ${GIT_TAG} == origin/* ]]; then
                ssh genie.fog05@projects-storage.eclipse.org rm -fr ${DOWNLOAD_DIR}
                fi
                ssh genie.fog05@projects-storage.eclipse.org mkdir -p ${DOWNLOAD_DIR}
                COMMIT_ID=`git log -n1 --format="%h"`
                echo "https://github.com/eclipse-fog05/fog05/tree/${COMMIT_ID}" > _git_commit_${COMMIT_ID}.txt
                scp _*.txt genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}/

                scp target/debian/*.deb genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}

            '''
            }
        }
        }

    }
}