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
    volumeMounts:
    - mountPath: "/home/jenkins"
      name: "jenkins-home"
      readOnly: false
    tty: true
    resources:
      limits:
        memory: "8Gi"
        cpu: "2"
      requests:
        memory: "8Gi"
        cpu: "2"
  - name: jnlp
    volumeMounts:
    - name: volume-known-hosts
      mountPath: /home/jenkins/.ssh
  volumes:
  - name: "jenkins-home"
    emptyDir: {}
  - name: volume-known-hosts
    configMap:
      name: known-hosts

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
        stage('[Install] rust') {
            steps {
                container('ubu20') {
                    sh '''
                        pwd
                        export  HOME=/home/$(id -u)
                        curl --proto "=https" --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- --default-toolchain nightly -y
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo

                        rustup target add aarch64-unknown-linux-gnu
                        rustup target add armv7-unknown-linux-gnueabihf

                        echo '[target.aarch64-unknown-linux-gnu]' >> /home/$(id -u)/.cargo/config
                        echo 'linker = "aarch64-linux-gnu-gcc"' >> /home/$(id -u)/.cargo/config
                        echo 'strip = { path = "aarch64-linux-gnu-strip" }' >> /home/$(id -u)/.cargo/config
                        echo 'objcopy = { path = "aarch64-linux-gnu-objcopy" }' >> /home/$(id -u)/.cargo/config
                        echo '[target.armv7-unknown-linux-gnueabihf]' >> /home/$(id -u)/.cargo/config
                        echo 'linker = "arm-linux-gnueabihf-gcc"' >> /home/$(id -u)/.cargo/config
                        echo 'strip = { path = "arm-linux-gnueabihf-strip" }' >> /home/$(id -u)/.cargo/config
                        echo 'objcopy = { path = "arm-linux-gnueabihf-objcopy" }' >> /home/$(id -u)/.cargo/config

                        cargo install cargo-deb
                    '''
                }
            }
        }

        stage('[Check] Dependencies') {
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo
                        cargo check
                    '''
                }
            }
        }


        stage('[Build] x86_64-unknown-linux-gnu') {
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo
                        cargo build --target=x86_64-unknown-linux-gnu --release --all-targets
                    '''
                }
            }
        }

        stage('[Build] aarch64-unknown-linux-gnu') {
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo

                        cargo build --target=aarch64-unknown-linux-gnu --release --all-targets
                    '''
                }
            }
        }

        stage('[Build] armv7-unknown-linux-gnueabihf') {
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo

                        cargo build --target=armv7-unknown-linux-gnueabihf --release --all-targets
                    '''
                }
            }
        }


        stage('[Package] x86_64-unknown-linux-gnu'){
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo

                        tar -czvf eclipse-fog05-${LABEL}-x86_64-unknown-linux-gnu.tgz --strip-components 3 target/x86_64-unknown-linux-gnu/release/fog05-agent target/x86_64-unknown-linux-gnu/release/fog05-fosctl
                        cargo deb --target=x86_64-unknown-linux-gnu -p fog05-agent --no-build
                        cargo deb --target=x86_64-unknown-linux-gnu  -p fog05-fosctl --no-build
                    '''
                }
            }
        }

        stage('[Package] aarch64-unknown-linux-gnu'){
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo

                        tar -czvf eclipse-fog05-${LABEL}-aarch64-unknown-linux-gnu.tgz --strip-components 3 target/aarch64-unknown-linux-gnu/release/fog05-agent target/aarch64-unknown-linux-gnu/release/fog05-fosctl
                        cargo deb --target=aarch64-unknown-linux-gnu -p fog05-agent --no-build
                        cargo deb --target=aarch64-unknown-linux-gnu  -p fog05-fosctl --no-build
                    '''
                }
            }
        }

        stage('[Package] armv7-unknown-linux-gnueabihf'){
            steps {
                container('ubu20') {
                    sh '''
                        export  HOME=/home/$(id -u)
                        export RUSTUP_HOME=/home/$(id -u)/.rustup
                        export PATH=$PATH:/home/$(id -u)/.cargo/bin
                        export CARGO_HOME=/home/$(id -u)/.cargo

                        tar -czvf eclipse-fog05-${LABEL}-armv7-unknown-linux-gnueabihf.tgz --strip-components 3 target/armv7-unknown-linux-gnueabihf/release/fog05-agent target/armv7-unknown-linux-gnueabihf/release/fog05-fosctl

                        cargo deb --target=armv7-unknown-linux-gnueabihf -p fog05-agent --no-build
                        cargo deb --target=armv7-unknown-linux-gnueabihf  -p fog05-fosctl --no-build
                    '''
                }
            }
        }

        stage('[Generate] Packages.gz') {
        when { expression { return params.PUBLISH_ECLIPSE_DOWNLOAD }}
        steps {
            container('ubu20') {
            sh '''
                cp target/x86_64-unknown-linux-gnu/debian/*.deb ./
                cp target/aarch64-unknown-linux-gnu/debian/*.deb ./
                cp target/armv7-unknown-linux-gnueabihf/debian/*.deb ./

                dpkg-scanpackages --multiversion . > Packages
                cat Packages
                gzip -c9 < Packages > Packages.gz
            '''
            }
        }
        }

        stage('[Publish] Upload packages to download.eclipse.org') {
        when { expression { return params.PUBLISH_ECLIPSE_DOWNLOAD }}
        steps {
            sshagent ( ['projects-storage.eclipse.org-bot-ssh']) {
            sh '''
                ssh genie.fog05@projects-storage.eclipse.org rm -fr ${DOWNLOAD_DIR}
                ssh genie.fog05@projects-storage.eclipse.org mkdir -p ${DOWNLOAD_DIR}
                COMMIT_ID=`git log -n1 --format="%h"`
                echo "https://github.com/eclipse-fog05/fog05/tree/${COMMIT_ID}" > _git_commit_${COMMIT_ID}.txt
                scp _*.txt genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}/

                scp eclipse-fog05-${LABEL}-x86_64-unknown-linux-gnu.tgz genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}
                scp eclipse-fog05-${LABEL}-aarch64-unknown-linux-gnu.tgz genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}
                scp eclipse-fog05-${LABEL}-armv7-unknown-linux-gnueabihf.tgz genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}

                scp target/x86_64-unknown-linux-gnu/debian/*.deb genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}
                scp target/aarch64-unknown-linux-gnu/debian/*.deb genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}
                scp target/armv7-unknown-linux-gnueabihf/debian/*.deb genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}

                scp Packages.gz genie.fog05@projects-storage.eclipse.org:${DOWNLOAD_DIR}/

            '''
            }
        }
        }

    }
}