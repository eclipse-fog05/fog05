package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"math/rand"
	"os"
	"runtime"
	"sync"
	"time"

	fog05 "github.com/eclipse-fog05/sdk-go/fog05sdk"

	fim "github.com/eclipse-fog05/api-go/fog05"
	"github.com/google/uuid"
	"github.com/juliangruber/go-intersect"
	log "github.com/sirupsen/logrus"

	//k8s
	"context"

	appsv1 "k8s.io/api/apps/v1"
	apiv1 "k8s.io/api/core/v1"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/util/yaml"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/rest"
	//debug
	// "github.com/davecgh/go-spew/spew"
)

const DEFAULTUUID string = "00000000-0000-0000-0000-000000000000"

const (
	ONBOARDING string = "ONBOARDING"
	ONBOARDED  string = "ONBOARDED"
	STARTING   string = "STARTING"
	RUNNING    string = "RUNNING"
	STOPPING   string = "STOPPING"
	STOPPED    string = "STOPPED"
	OFFLOADING string = "OFFLOADING"
	OFFLOADED  string = "OFFLOADED"
	INVALID    string = "INVALID"
	ERROR      string = "ERROR"
	RECOVERING string = "RECOVERING"
)

func getFrame(skipFrames int) runtime.Frame {
	// We need the frame at index skipFrames+2, since we never want runtime.Callers and getFrame
	targetFrameIndex := skipFrames + 2

	// Set size to targetFrameIndex+2 to ensure we have room for one more caller than we need
	programCounters := make([]uintptr, targetFrameIndex+2)
	n := runtime.Callers(0, programCounters)

	frame := runtime.Frame{Function: "unknown"}
	if n > 0 {
		frames := runtime.CallersFrames(programCounters[:n])
		for more, frameIndex := true, 0; more && frameIndex <= targetFrameIndex; frameIndex++ {
			var frameCandidate runtime.Frame
			frameCandidate, more = frames.Next()
			if frameIndex == targetFrameIndex {
				frame = frameCandidate
			}
		}
	}

	return frame
}

// MyCaller returns the caller of the function that called it :)
func MyCaller() (string, int) {
	// Skip GetCallerFunctionName and the function to get the caller of
	return getFrame(2).Function, getFrame(2).Line
}

type EnqueuedJob struct {
	Job      fog05.Job
	systemid string
	tenantid string
}

type EntityActionBody struct {
	UUID    string  `json:"uuid"`
	FIMID   *string `json:"fim_id"`
	CloudID *string `json:"cloud_id"`
}

type OrchestratorState struct {
	connectors map[string]map[string]*fog05.FOrcEZConnector
	fims       map[string]map[string]map[string]*fim.FIMAPI
	clouds     map[string]map[string]map[string]*kubernetes.Clientset
	rwLock     sync.RWMutex
}

type FOrcE struct {
	sigs     chan os.Signal
	done     chan bool
	state    *OrchestratorState
	jobQueue chan EnqueuedJob
	zlocator string
	logger   *log.Logger
}

//NewFOrcE ...
func NewFOrcE(locator string) (*FOrcE, error) {

	state := &OrchestratorState{
		connectors: map[string]map[string]*fog05.FOrcEZConnector{},
		fims:       map[string]map[string]map[string]*fim.FIMAPI{},
		clouds:     map[string]map[string]map[string]*kubernetes.Clientset{},
	}

	f := &FOrcE{
		state:    state,
		sigs:     make(chan os.Signal, 1),
		done:     make(chan bool, 1),
		jobQueue: make(chan EnqueuedJob, 1024),
		zlocator: locator,
		logger:   log.New(),
	}
	//adding by default SysID 0 Tenant 0
	err := f.AddSystem(DEFAULTUUID)
	if f.check(err) {
		return nil, err
	}

	return f, nil
}

//Init Initializes the FOrcE orchestartor using information stored in Zenoh
func (f *FOrcE) Init() error {
	f.logger.Info("Initializing Orchestartor from Zenoh")
	//f.state.rwLock.Lock()
	//defer f.state.rwLock.Unlock()
	c, _ := f.state.connectors[DEFAULTUUID][DEFAULTUUID]
	zFIMs, _ := c.Orchestrator.GetAllFIMsInfo()
	// if f.check(err) {
	// 	return err
	// }
	for _, fimInfo := range zFIMs {
		f.logger.Info(fmt.Sprintf("Initializing Adding FIM: %s", fimInfo.UUID))
		err := f.AddFIM(DEFAULTUUID, DEFAULTUUID, fimInfo.UUID, fimInfo.Locator)
		if f.check(err) {
			return err
		}
	}
	zClouds, _ := c.Orchestrator.GetAllCloudsInfo()
	// if f.check(err) {
	// 	return err
	// }
	for _, cloudInfo := range zClouds {
		f.logger.Info(fmt.Sprintf("Initializing Adding Cloud: %s", cloudInfo.UUID))
		kubeConfig := &rest.Config{}
		err := json.Unmarshal([]byte(cloudInfo.Config), kubeConfig)

		err = f.AddCloud(DEFAULTUUID, DEFAULTUUID, cloudInfo.UUID, cloudInfo.Config, kubeConfig.CAData, kubeConfig.KeyData, kubeConfig.CertData)
		if f.check(err) {
			return err
		}
	}

	instances, _ := c.Orchestrator.GetAllEntityRecordsInfo("*")
	// if f.check(err) {
	// 	return err
	// }
	for _, instance := range instances {
		f.logger.Info(fmt.Sprintf("Initializing Adding Monitoring goroutine for: %s", instance.UUID))
		go f.monitoringJobsSpawner(c, DEFAULTUUID, DEFAULTUUID, instance.UUID, instance.FIMID, instance.CloudID)
	}

	jobs, _ := c.Orchestrator.GetAllJobsInfo()
	// if f.check(err) {
	// 	return err
	// }
	for _, job := range jobs {

		switch job.Status {
		case "queued":
			f.logger.Info(fmt.Sprintf("Initializing Adding Job: %s", job.JobID))
			qJob := EnqueuedJob{
				Job:      job,
				systemid: DEFAULTUUID,
				tenantid: DEFAULTUUID,
			}
			f.jobQueue <- qJob
		// case RUNNING:
		// 	job.Status = "queued"
		// 	f.logger.Info(fmt.Sprintf("Initializing Adding Job: %s that was running...", job.JobID))
		// 	qJob := EnqueuedJob{
		// 		Job:      job,
		// 		systemid: DEFAULTUUID,
		// 		tenantid: DEFAULTUUID,
		// 	}
		// 	f.jobQueue <- qJob
		default:
			f.logger.Info(fmt.Sprintf("Initializing not adding Job: %s because status is %s", job.JobID, job.Status))
		}
	}

	f.logger.Info("Initialization done! Orchestrator is ready")
	return nil

}

// Start starts the FOrcE orchestrator
func (f *FOrcE) Start() {
	go f.JobScheduler()
}

func (f *FOrcE) check(err error) bool {
	if err != nil {
		fun, line := MyCaller()
		f.logger.Error(fmt.Sprintf("FOrcE Error Check got: %s Called by %s:%d", err.Error(), fun, line))
		return true
	}
	return false
}

//AddSystem adds a system with the default tenant 0
func (f *FOrcE) AddSystem(sysid string) error {

	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if _, exists := f.state.connectors[sysid]; exists {
		return fmt.Errorf("System %s exists", sysid)
	}

	c, err := fog05.NewFOrcEZConnector(f.zlocator, sysid, DEFAULTUUID)
	if f.check(err) {
		return err
	}
	f.state.connectors[sysid] = map[string]*fog05.FOrcEZConnector{
		DEFAULTUUID: c,
	}
	f.state.fims[sysid] = map[string]map[string]*fim.FIMAPI{
		DEFAULTUUID: map[string]*fim.FIMAPI{},
	}
	f.state.clouds[sysid] = map[string]map[string]*kubernetes.Clientset{
		DEFAULTUUID: map[string]*kubernetes.Clientset{},
	}
	return nil
}

//GetSystems get all the available systems
func (f *FOrcE) GetSystems() []string {
	f.state.rwLock.RLock()
	defer f.state.rwLock.RUnlock()
	systems := []string{}
	for k := range f.state.connectors {
		systems = append(systems, k)
	}
	return systems
}

//RemoveSystem removes a system and all its tenants
func (f *FOrcE) RemoveSystem(sysid string) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()
	if s, exists := f.state.connectors[sysid]; exists {
		for _, c := range s {
			err := c.Close()
			if f.check(err) {
				return err
			}
		}
		delete(f.state.connectors, sysid)
		return nil
	}

	return fmt.Errorf("System %s does not exists", sysid)

}

//AddTenant adds tenant to an existing system
func (f *FOrcE) AddTenant(sysid string, tenantid string) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if _, exists = s[tenantid]; exists {
			return fmt.Errorf("Tenant %s exists", tenantid)
		}
		c, err := fog05.NewFOrcEZConnector(f.zlocator, sysid, tenantid)
		if f.check(err) {
			return err
		}
		s[tenantid] = c
		f.state.fims[sysid] = map[string]map[string]*fim.FIMAPI{
			tenantid: map[string]*fim.FIMAPI{},
		}
		f.state.clouds[sysid] = map[string]map[string]*kubernetes.Clientset{
			tenantid: map[string]*kubernetes.Clientset{},
		}
		return nil
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//GetTenants get all the available tenants in the system
func (f *FOrcE) GetTenants(sysid string) ([]string, error) {
	f.state.rwLock.RLock()
	defer f.state.rwLock.RUnlock()

	if s, exists := f.state.connectors[sysid]; exists {
		tenants := []string{}
		for k := range s {
			tenants = append(tenants, k)
		}
		return tenants, nil
	}
	return []string{}, fmt.Errorf("System %s does not exists", sysid)
}

//RemoveTenant removes a tenant from an existing system
func (f *FOrcE) RemoveTenant(sysid string, tenantid string) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			err := c.Close()
			if f.check(err) {
				return err
			}
			delete(s, tenantid)
			return nil
		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//AddFIM adds a FIM to this Orchestrator
func (f *FOrcE) AddFIM(sysid string, tenantid string, fimid string, locator string) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			if _, exists := f.state.fims[sysid][tenantid][fimid]; exists {
				return fmt.Errorf("FIM %s exists", fimid)
			}
			fimapi, err := fim.NewFIMAPI(locator, nil, nil)
			if f.check(err) {
				return err
			}
			f.state.fims[sysid][tenantid][fimid] = fimapi
			fimInfo := fog05.FIMInfo{
				UUID:    fimid,
				Locator: locator,
			}
			f.check(c.Orchestrator.AddFIMInfo(fimInfo))

			return nil
		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//GetFIMs get all the available FIMs
func (f *FOrcE) GetFIMs(sysid string, tenantid string) ([]string, error) {
	f.state.rwLock.RLock()
	defer f.state.rwLock.RUnlock()

	fims := []string{}
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {

			for k := range f.state.fims[sysid][tenantid] {
				// 	fims = append(fims, k)
				fi, err := c.Orchestrator.GetFIMInfo(k)
				if f.check(err) {
					return fims, err
				}
				fims = append(fims, fi.UUID)
			}
			return fims, nil
		}
		return fims, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fims, fmt.Errorf("System %s does not exists", sysid)

}

//GetFIM get the given FIM
func (f *FOrcE) GetFIM(sysid string, tenantid string, fimid string) (*fog05.FIMInfo, error) {
	f.state.rwLock.RLock()
	defer f.state.rwLock.RUnlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			fi, err := c.Orchestrator.GetFIMInfo(fimid)
			if f.check(err) {
				return nil, err
			}
			return fi, nil
		}
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return nil, fmt.Errorf("System %s does not exists", sysid)

}

//RemoveFIM removes a FIM
func (f *FOrcE) RemoveFIM(sysid string, tenantid string, fimid string) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			if fimapi, exists := f.state.fims[sysid][tenantid][fimid]; exists {
				fimapi.Close()
				delete(f.state.fims[sysid][tenantid], fimid)
				f.check(c.Orchestrator.RemoveFIMInfo(fimid))
				return nil
			}

			return fmt.Errorf("FIM %s does not exists", fimid)
		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//AddCloud adds a K8s client to this orchestrator
func (f *FOrcE) AddCloud(sysid string, tenantid string, cloudid string, kubeconfig string, caData []byte, certData []byte, keyData []byte) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			if _, exists := f.state.clouds[sysid][tenantid][cloudid]; exists {
				return fmt.Errorf("Cloud %s exists", cloudid)
			}
			k8sConfig := &rest.Config{}
			dec := yaml.NewYAMLOrJSONDecoder(bytes.NewReader([]byte(kubeconfig)), 65535)
			err := dec.Decode(&k8sConfig)
			// k8sConfig, err := clientcmd.BuildConfigFromFlags("", kubeconfig)
			if f.check(err) {
				return err
			}
			//storing CA, Cert and Key data into config
			k8sConfig.CAData = caData
			k8sConfig.KeyData = keyData
			k8sConfig.CertData = certData

			k8sClientset, err := kubernetes.NewForConfig(k8sConfig)
			if f.check(err) {
				return err
			}

			d, err := json.Marshal(&k8sConfig)
			if f.check(err) {
				return err
			}
			f.state.clouds[sysid][tenantid][cloudid] = k8sClientset
			cloudInfo := fog05.CloudInfo{
				UUID:   cloudid,
				Config: string(d),
			}
			f.check(c.Orchestrator.AddCloudInfo(cloudInfo))

			return nil
		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//GetClouds get all the available K8s clients
func (f *FOrcE) GetClouds(sysid string, tenantid string) ([]string, error) {
	f.state.rwLock.RLock()
	defer f.state.rwLock.RUnlock()

	clouds := []string{}
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			for k := range f.state.clouds[sysid][tenantid] {
				ci, err := c.Orchestrator.GetCloudInfo(k)
				if f.check(err) {
					return clouds, err
				}
				clouds = append(clouds, ci.UUID)
			}
			return clouds, nil
		}
		return clouds, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return clouds, fmt.Errorf("System %s does not exists", sysid)
}

//GetCloud get the given K8s cloud
func (f *FOrcE) GetCloud(sysid string, tenantid string, cloudid string) (*fog05.CloudInfo, error) {
	f.state.rwLock.RLock()
	defer f.state.rwLock.RUnlock()
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {

			ci, err := c.Orchestrator.GetCloudInfo(cloudid)
			if f.check(err) {
				return nil, err
			}
			return ci, nil
		}
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return nil, fmt.Errorf("System %s does not exists", sysid)

}

//RemoveCloud removes a K8s client
func (f *FOrcE) RemoveCloud(sysid string, tenantid string, cloudid string) error {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			if _, exists := f.state.clouds[sysid][tenantid][cloudid]; exists {
				// k8sClient.Close()
				delete(f.state.clouds[sysid][tenantid], cloudid)
				f.check(c.Orchestrator.RemoveCloudInfo(cloudid))
				return nil
			}

			return fmt.Errorf("Cloud %s does not exists", cloudid)
		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

// Jobs

//InsertNewJob inserts a new job in the job queue if there is space
func (f *FOrcE) InsertNewJob(sysid string, tenantid string, jobRequest fog05.RequestNewJobMessage) (*fog05.ReplyNewJobMessage, error) {
	//f.mux.Lock()
	//defer f.mux.Unlock()
	f.state.rwLock.RLock()
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {

			f.state.rwLock.RUnlock()

			jid := uuid.New().String()
			job := fog05.Job{
				OriginalSender: jobRequest.Sender,
				JobKind:        jobRequest.JobKind,
				Body:           jobRequest.Body,
				Status:         "queued",
				JobID:          jid,
			}
			eJob := EnqueuedJob{
				Job:      job,
				systemid: sysid,
				tenantid: tenantid,
			}

			select {
			case f.jobQueue <- eJob:
				f.logger.Info(fmt.Sprintf("Job: %s added to queue", jid))
				reply := fog05.ReplyNewJobMessage{
					OriginalSender: jobRequest.Sender,
					JobID:          jid,
					Accepted:       true,
				}
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return &reply, nil
			default:
				f.logger.Info(fmt.Sprintf("Unable to enqueue job: %s, channel is full!", jid))
				reply := fog05.ReplyNewJobMessage{
					OriginalSender: jobRequest.Sender,
					JobID:          jid,
					Accepted:       false,
				}
				return &reply, nil
			}
		}
		f.state.rwLock.RUnlock()
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	f.state.rwLock.RUnlock()
	return nil, fmt.Errorf("System %s does not exists", sysid)
}

//GetJob gets information about the given entity from the catalog
func (f *FOrcE) GetJob(sysid string, tenantid string, jid string) (*fog05.Job, error) {
	f.state.rwLock.RLock()
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			f.state.rwLock.RUnlock()
			info, err := c.Orchestrator.GetJobInfo(jid)
			if f.check(err) {
				return nil, err
			}
			return info, nil

		}
		f.state.rwLock.RUnlock()
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	f.state.rwLock.RUnlock()
	return nil, fmt.Errorf("System %s does not exists", sysid)
}

//JobScheduler ...
func (f *FOrcE) JobScheduler() {
	f.logger.Info("Starting job scheduler task...")
	for {
		for qJob := range f.jobQueue {
			f.logger.Info(fmt.Sprintf("Got job from queue: %+v", qJob))
			switch qJob.Job.JobKind {
			/*
			* JobKind can be:
			* ONBOARD -> add the descriptor into the catalog
			* OFFLOAD -> remove the descriptor from the catalog
			* INSTANTIATE -> instantiate the given Entity
			* TEARDOWN -> remove the given entity
			* MONITORING -> recurrent job that verifies the status of the entities
			*
			* Job Status:
			* Queued
			* Running
			* Completed
			* Failed
			 */
			case "test":
				go f.testWorker(qJob)
			case "onboard":
				go f.onboardWorker(qJob)
			case "offload":
				go f.offloadWorker(qJob)
			case "instantiate":
				go f.instantiateWorker(qJob)
			case "monitoring":
				go f.monitoringWorker(qJob)
			case "teardown":
				go f.teardownWorker(qJob)
			default:
				go f.errorWorker(qJob)
			}
		}
	}
}

// Worker functions...

func (f *FOrcE) testWorker(qJob EnqueuedJob) {

	f.logger.Info(fmt.Sprintf("Running a \"test\" Job, it sleeps 45s JobID: %s", qJob.Job.JobID))
	job := qJob.Job
	f.state.rwLock.RLock()
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		if c, exists := s[qJob.tenantid]; exists {
			job.Status = RUNNING
			f.logger.Info(fmt.Sprintf("Test Job: %+v", job))
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)
			time.Sleep(45 * time.Second)
			job.Status = "completed"
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)
			f.logger.Info(fmt.Sprintf("Test Job: %s done", qJob.Job.JobID))
			return
		}
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return

}

func (f *FOrcE) errorWorker(qJob EnqueuedJob) {

	f.logger.Error(fmt.Sprintf("Running error Job: %+v", qJob.Job))
	job := qJob.Job
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		if c, exists := s[qJob.tenantid]; exists {
			f.state.rwLock.RUnlock()
			job.Status = "failed"
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)
			return
		}
		f.state.rwLock.RUnlock()
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.state.rwLock.RUnlock()
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return

}

func (f *FOrcE) onboardWorker(qJob EnqueuedJob) {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()
	f.logger.Info(fmt.Sprintf("Running Onboarding Job, JobID: %s", qJob.Job.JobID))
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		if c, exists := s[qJob.tenantid]; exists {
			job := qJob.Job

			job.Status = RUNNING
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)

			//Getting the descriptor from the body
			entityDescriptor := fog05.EntityDescriptor{}
			err = json.Unmarshal([]byte(job.Body), &entityDescriptor)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}
			//Populate UUIDs
			if entityDescriptor.UUID == nil {
				eUUID := uuid.New().String()
				entityDescriptor.UUID = &eUUID
			}

			for i := 0; i < len(entityDescriptor.FDUs); i++ {
				fdu := &entityDescriptor.FDUs[i]
				if fdu.UUID == nil {
					fduUUID := uuid.New().String()
					fdu.UUID = &fduUUID
				}
			}

			for i := 0; i < len(entityDescriptor.VirtualLinks); i++ {
				vl := &entityDescriptor.VirtualLinks[i]
				if vl.UUID == nil {
					vlUUID := uuid.New().String()
					vl.UUID = &vlUUID
				}
			}

			v, err := json.Marshal(entityDescriptor)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			job.Body = string(v)
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)

			err = f.AddEntity(qJob.systemid, qJob.tenantid, entityDescriptor)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			job.Status = "completed"
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)
			f.logger.Info(fmt.Sprintf("Onboarding Job: %s done", qJob.Job.JobID))
			return
		}
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return

}

func (f *FOrcE) offloadWorker(qJob EnqueuedJob) {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	f.logger.Info(fmt.Sprintf("Running Offloading Job, JobID: %s", qJob.Job.JobID))
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		if c, exists := s[qJob.tenantid]; exists {
			job := qJob.Job

			job.Status = RUNNING
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)

			//Getting the descriptor from the body
			info := EntityActionBody{}
			err = json.Unmarshal([]byte(job.Body), &info)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			entityDescriptor, err := c.Orchestrator.GetEntityInfo(info.UUID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			for i := 0; i < len(entityDescriptor.FDUs); i++ {
				fdu := &entityDescriptor.FDUs[i]
				err = c.Orchestrator.RemoveFDUInfo(*fdu.UUID)
				f.check(err)
			}

			for i := 0; i < len(entityDescriptor.VirtualLinks); i++ {
				vl := &entityDescriptor.VirtualLinks[i]
				err = c.Orchestrator.RemoveVirtualLinkInfo(*vl.UUID)
				f.check(err)
			}

			err = f.RemoveEntity(qJob.systemid, qJob.tenantid, info.UUID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			job.Status = "completed"
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)
			f.logger.Info(fmt.Sprintf("Offloading Job: %s done", qJob.Job.JobID))
			return
		}
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return

}

func (f *FOrcE) instantiateWorker(qJob EnqueuedJob) {

	f.state.rwLock.RLock()
	f.logger.Info(fmt.Sprintf("Running Instantiation Job, JobID: %s", qJob.Job.JobID))
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		f.state.rwLock.RUnlock()
		if c, exists := s[qJob.tenantid]; exists {
			job := qJob.Job

			job.Status = RUNNING
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)

			//Getting the descriptor from the body
			info := EntityActionBody{}
			err = json.Unmarshal([]byte(job.Body), &info)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			entityDescriptor, err := c.Orchestrator.GetEntityInfo(info.UUID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			//Should create and instance UUID and record
			entityInstanceUUID := uuid.New().String()
			entityRecord := fog05.EntityRecord{
				ID:           *entityDescriptor.UUID,
				UUID:         entityInstanceUUID,
				Status:       ONBOARDING,
				FDUs:         []string{},
				VirtualLinks: []string{},
				CloudID:      info.CloudID,
				FIMID:        info.FIMID,
			}

			v, err := json.Marshal(entityRecord)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}
			job.Body = string(v)
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)

			//Storing initial record on Zenoh
			err = c.Orchestrator.AddEntityRecord(entityRecord)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			//First create the virtual links into the FIM
			for i := 0; i < len(entityDescriptor.VirtualLinks); i++ {
				if info.FIMID == nil {
					job.Status = "failed"
					err := c.Orchestrator.AddJobInfo(job)
					f.check(err)
					return
				}

				fimapi, exists := f.state.fims[qJob.systemid][qJob.tenantid][*info.FIMID]
				if !exists {
					f.logger.Info(fmt.Sprintf("JobID: %s FIM %s not exists", qJob.Job.JobID, *info.FIMID))
					job.Status = "failed"
					err := c.Orchestrator.AddJobInfo(job)
					f.check(err)
					entityRecord.Status = "invalid"
					f.check(c.Orchestrator.AddEntityRecord(entityRecord))
					return
				}

				vl := *&entityDescriptor.VirtualLinks[i]
				f.logger.Info(fmt.Sprintf("JobID: %s Adding Virtual Link %+v", qJob.Job.JobID, vl))
				vlAddrInfo := fog05.AddressInformation{
					IPVersion:  vl.IPVersion,
					Subnet:     *vl.IPConfiguration.Subnet,
					Gateway:    vl.IPConfiguration.Gateway,
					DHCPEnable: true,
					DHCPRange:  vl.IPConfiguration.DHCPRange,
					DNS:        vl.IPConfiguration.DNS,
				}
				vlFIM := fog05.VirtualNetwork{
					UUID:            uuid.New().String(),
					Name:            *vl.UUID,
					NetworkType:     "ELAN",
					IPConfiguration: &vlAddrInfo,
				}

				err = fimapi.Network.AddNetwork(vlFIM)
				if f.check(err) {
					job.Status = "failed"
					err := c.Orchestrator.AddJobInfo(job)
					f.check(err)
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(entityRecord))
					return
				}

				entityRecord.VirtualLinks = append(entityRecord.VirtualLinks, vlFIM.UUID)
				time.Sleep(1 * time.Second)

			}

			//Orders the FDU following the DependsON
			orderedFDUs := f.orderFDUs(entityDescriptor.FDUs)

			for i := 0; i < len(orderedFDUs); i++ {

				fdu := &orderedFDUs[i]
				if fdu.Hypervisor == "cloud" {

					if info.CloudID == nil {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}

					f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s is Cloud FDU", qJob.Job.JobID, info.UUID, *fdu.UUID))

					clientset, exists := f.state.clouds[qJob.systemid][qJob.tenantid][*info.CloudID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s Cloud %s not exists", qJob.Job.JobID, *info.CloudID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}

					deploymentsClient := clientset.AppsV1().Deployments(apiv1.NamespaceDefault)
					// f.logger.Info(fmt.Sprintf("JobID: %s Deployment Client %%", qJob.Job.JobID, spew.Sdump(deploymentsClient)))
					deployment := &appsv1.Deployment{}
					depDesc, err := base64.StdEncoding.DecodeString(*fdu.HypervisorSpecific)
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = "invalid"
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}
					dec := yaml.NewYAMLOrJSONDecoder(bytes.NewReader(depDesc), 65535)
					err = dec.Decode(&deployment)
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = "invalid"
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}
					deployment.ObjectMeta.Name = uuid.New().String()
					f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s K8s deployment: %+v", qJob.Job.JobID, info.UUID, *fdu.UUID, deployment))
					res, err := deploymentsClient.Create(context.TODO(), deployment, metav1.CreateOptions{})
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}
					f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s K8s deployment: %+v", qJob.Job.JobID, info.UUID, *fdu.UUID, res))
					entityRecord.FDUs = append(entityRecord.FDUs, deployment.ObjectMeta.Name)

					fduRecord := fog05.FOrcEFDURecord{
						UUID:   deployment.ObjectMeta.Name,
						ID:     *fdu.UUID,
						Status: STARTING,
					}
					f.check(c.Orchestrator.AddFDURecord(fduRecord))

				} else {
					if info.FIMID == nil {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}
					fimapi, exists := f.state.fims[qJob.systemid][qJob.tenantid][*info.FIMID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s FIM %s not exists", qJob.Job.JobID, *info.FIMID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}

					f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s is FIM FDU of Kind %s", qJob.Job.JobID, info.UUID, *fdu.UUID, fdu.Hypervisor))

					//Converting the Orchestrator FDU to FIM FDU
					// This will change in the future the descriptors will be alligned

					fduFIMInterfaces := []fog05.FDUInterfaceDescriptor{}
					fduFIMConnectionPoints := []fog05.ConnectionPointDescriptor{}

					for _, intf := range fdu.Interfaces {
						vpci := ""
						if intf.VirtualInterface.Parent != nil {
							vpci = *intf.VirtualInterface.Parent
						}
						bw := 100
						if intf.VirtualInterface.Bandwidth != nil {
							bw = int(*intf.VirtualInterface.Bandwidth)
						}

						fimIntf := fog05.FDUInterfaceDescriptor{
							Name:          intf.Name,
							InterfaceType: fog05.INTERNAL,
							IsMGMT:        false,
							MACAddress:    intf.MACAddress,
							CPID:          intf.CPID,
							VirtualInterface: fog05.FDUVirtualInterface{
								InterfaceType: intf.VirtualInterface.InterfaceKind,
								VPCI:          vpci,
								Bandwidth:     bw,
							},
						}
						fduFIMInterfaces = append(fduFIMInterfaces, fimIntf)
					}

					for _, cp := range fdu.ConnectionPoints {

						vldID := ""
						for _, vl := range entityDescriptor.VirtualLinks {
							if vl.ID == cp.VLDRef {
								vldID = *vl.UUID
							}
						}
						if vldID == "" {
							f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s Virtual Link Reference %s is broken for FDU %s", qJob.Job.JobID, cp.VLDRef, *fdu.UUID))
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}

						fimVLDRef, err := f.getFIMNetworkID(vldID, fimapi)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}

						fimCP := fog05.ConnectionPointDescriptor{
							UUID:   cp.UUID,
							ID:     cp.ID,
							Name:   cp.Name,
							VLDRef: &fimVLDRef,
						}

						fduFIMConnectionPoints = append(fduFIMConnectionPoints, fimCP)
					}

					fimFDU := fog05.FDU{
						ID:          fdu.ID,
						UUID:        fdu.UUID,
						Name:        fdu.Name,
						Description: fdu.Description,
						Image:       fdu.Image,
						Hypervisor:  fdu.Hypervisor,
						ComputationRequirements: fog05.FDUComputationalRequirements{
							CPUArch:         fdu.ComputationRequirements.CPUArch,
							CPUMinFrequency: fdu.ComputationRequirements.CPUMinFrequency,
							CPUMinCount:     fdu.ComputationRequirements.CPUMinCount,
							RAMSizeMB:       float64(fdu.ComputationRequirements.RAMSizeMB),
							StorageSizeGB:   float64(fdu.ComputationRequirements.StorageSizeMB) / 1024,
						},
						Storage:          []fog05.FDUStorageDescriptor{},
						MigrationKind:    "COLD",
						DependsOn:        fdu.DependsOn,
						IOPorts:          []fog05.FDUIOPort{},
						Interfaces:       fduFIMInterfaces,
						ConnectionPoints: fduFIMConnectionPoints,
					}

					//Stores the descriptor in the FIM
					f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s Storing in FIM %+v", qJob.Job.JobID, info.UUID, *fdu.UUID, fimFDU))
					_, err = fimapi.FDU.Onboard(fimFDU)
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(entityRecord))
						return
					}

					entityRecord.Status = STARTING
					f.check(c.Orchestrator.AddEntityRecord(entityRecord))

					instances := []string{}
					minReplicas := uint8(1)
					if fdu.Replicas != nil {
						minReplicas = *fdu.Replicas
					}

					f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s Needed Replicas: %d", qJob.Job.JobID, info.UUID, *fdu.UUID, minReplicas))

					for i := uint8(0); i < minReplicas; i++ {
						//Finds a node for the FDU
						nodeid, err := f.findFIMNode(&fimFDU, fimapi)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}
						f.logger.Info(fmt.Sprintf("JobID: %s EntityID: %s FDU: %s Node: %s", qJob.Job.JobID, info.UUID, *fdu.UUID, nodeid))
						fimInstance, err := fimapi.FDU.Define(nodeid, *fimFDU.UUID)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}

						instances = append(instances, fimInstance.UUID)

						_, err = fimapi.FDU.Configure(fimInstance.UUID)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}
						_, err = fimapi.FDU.Start(fimInstance.UUID, nil)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}
						fimInstance, err = fimapi.FDU.InstanceInfo(fimInstance.UUID)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(entityRecord))
							return
						}
						fduRecord := fog05.FOrcEFDURecord{
							UUID:   fimInstance.UUID,
							ID:     fimInstance.FDUID,
							Status: fimInstance.Status,
						}
						f.check(c.Orchestrator.AddFDURecord(fduRecord))
					}

					entityRecord.FDUs = append(entityRecord.FDUs, instances...)

				}

			}

			//Storing record in Orchestrator catalog
			entityRecord.Status = STARTING
			f.check(c.Orchestrator.AddEntityRecord(entityRecord))

			v, err = json.Marshal(entityRecord)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			job.Status = "completed"
			job.Body = string(v)
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)
			f.logger.Info(fmt.Sprintf("Instantiation Job: %s done", qJob.Job.JobID))

			go f.monitoringJobsSpawner(c, qJob.systemid, qJob.tenantid, entityRecord.UUID, info.FIMID, info.CloudID)

			return
		}
		f.state.rwLock.RUnlock()
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.state.rwLock.RUnlock()
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return

}

func (f *FOrcE) teardownWorker(qJob EnqueuedJob) {
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	f.logger.Info(fmt.Sprintf("Running Teardown Job, JobID: %s", qJob.Job.JobID))
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		if c, exists := s[qJob.tenantid]; exists {

			job := qJob.Job

			job.Status = RUNNING
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)

			//Getting the descriptor from the body
			info := EntityActionBody{}
			err = json.Unmarshal([]byte(job.Body), &info)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			entityRecord, err := c.Orchestrator.FindEntityInstanceInfo(info.UUID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			entityRecord.Status = STOPPING
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

			entityID := entityRecord.ID
			entityDescriptor, err := c.Orchestrator.GetEntityInfo(entityID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}
			f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s FDUs %+v", qJob.Job.JobID, entityRecord.UUID, entityRecord.FDUs))
			for _, fdu := range entityRecord.FDUs {

				fduDesc, err := f.findFDUForInstance(c, fdu)
				if f.check(err) {
					job.Status = "failed"
					err := c.Orchestrator.AddJobInfo(job)
					f.check(err)
					return
				}

				if fduDesc.Hypervisor == "cloud" {
					clientset, exists := f.state.clouds[qJob.systemid][qJob.tenantid][*entityRecord.CloudID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s Cloud %s not exists", qJob.Job.JobID, *entityRecord.CloudID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						return
					}

					deploymentsClient := clientset.AppsV1().Deployments(apiv1.NamespaceDefault)
					deletePolicy := metav1.DeletePropagationForeground
					err = deploymentsClient.Delete(context.TODO(), fdu, metav1.DeleteOptions{
						PropagationPolicy: &deletePolicy,
					})
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						return
					}
					c.Orchestrator.RemoveFDURecord(*fduDesc.UUID, fdu)

				} else {
					fimapi, exists := f.state.fims[qJob.systemid][qJob.tenantid][*entityRecord.FIMID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s FIM %s not exists", qJob.Job.JobID, *entityRecord.FIMID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						return
					}

					f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s Entity: %s FDU Instance: %s Stopping", qJob.Job.JobID, entityRecord.UUID, entityRecord.ID, fdu))
					fduInstanceInfo, _ := fimapi.FDU.InstanceInfo(fdu)
					fimapi.FDU.Stop(fdu)
					fimapi.FDU.Clean(fdu)
					fimapi.FDU.Undefine(fdu)
					c.Orchestrator.RemoveFDURecord(fduInstanceInfo.FDUID, fdu)
				}

			}

			entityRecord.Status = OFFLOADING
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

			for _, fdu := range entityDescriptor.FDUs {

				if fdu.Hypervisor != "cloud" {
					fimapi, exists := f.state.fims[qJob.systemid][qJob.tenantid][*entityRecord.FIMID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s FIM %s not exists", qJob.Job.JobID, *entityRecord.FIMID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						return
					}
					f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s Entity: %s FDU: %s Removing from FIM", qJob.Job.JobID, entityRecord.UUID, entityRecord.ID, *fdu.UUID))
					fimapi.FDU.Offload(*fdu.UUID)
				}

			}

			for _, net := range entityRecord.VirtualLinks {
				fimapi, exists := f.state.fims[qJob.systemid][qJob.tenantid][*entityRecord.FIMID]
				if !exists {
					f.logger.Info(fmt.Sprintf("JobID: %s FIM %s not exists", qJob.Job.JobID, *entityRecord.FIMID))
					job.Status = "failed"
					err := c.Orchestrator.AddJobInfo(job)
					f.check(err)
					return
				}

				nodes, _ := fimapi.Node.List()
				for _, n := range nodes {
					fimapi.Network.RemoveNetworkFromNode(n, net)
				}
				fimapi.Network.RemoveNetwork(net)

			}

			entityRecord.Status = OFFLOADED
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

			v, err := json.Marshal(entityRecord)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			job.Status = "completed"
			job.Body = string(v)
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)

			f.logger.Info(fmt.Sprintf("Teardown Job: %s done", qJob.Job.JobID))
			return
		}
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return
}

func (f *FOrcE) recoverWorker(entityRecord *fog05.EntityRecord, fimapi *fim.FIMAPI, cloud *kubernetes.Clientset, c *fog05.FOrcEZConnector) {

	entityRecord.Status = RECOVERING
	f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

	entityID := entityRecord.ID
	entityDescriptor, err := c.Orchestrator.GetEntityInfo(entityID)
	if f.check(err) {
		entityRecord.Status = ERROR
		f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
		return
	}

	//Should first verify virtual networks
	for _, net := range entityDescriptor.VirtualLinks {
		if fimapi == nil {
			f.logger.Error("FIMAPI is nil with Virtual Links!!")
			entityRecord.Status = ERROR
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
			return
		}
		apiNets, err := f.getFIMNetworkIDs(net.ID, fimapi)
		if f.check(err) {
			entityRecord.Status = ERROR
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
			return
		}

		entityVLs := []string{}
		intersection := intersect.Hash(apiNets, entityRecord.VirtualLinks).([]interface{})
		for _, v := range intersection {
			entityVLs = append(entityVLs, fmt.Sprint(v))
		}

		for len(entityDescriptor.VirtualLinks) > len(entityVLs) {
			f.logger.Info(fmt.Sprintf("Recovering Instance %s Adding Virtual Link %+v", entityRecord.UUID, net))
			vlAddrInfo := fog05.AddressInformation{
				IPVersion:  net.IPVersion,
				Subnet:     *net.IPConfiguration.Subnet,
				Gateway:    net.IPConfiguration.Gateway,
				DHCPEnable: true,
				DHCPRange:  net.IPConfiguration.DHCPRange,
				DNS:        net.IPConfiguration.DNS,
			}
			vlFIM := fog05.VirtualNetwork{
				UUID:            uuid.New().String(),
				Name:            *net.UUID,
				NetworkType:     "ELAN",
				IPConfiguration: &vlAddrInfo,
			}

			err = fimapi.Network.AddNetwork(vlFIM)
			if f.check(err) {
				entityRecord.Status = ERROR
				f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
				return
			}

			entityRecord.VirtualLinks = append(entityRecord.VirtualLinks, vlFIM.UUID)
			entityVLs = append(entityVLs, vlFIM.UUID)
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
			time.Sleep(1 * time.Second)
		}

	}

	for _, fdu := range entityDescriptor.FDUs {
		if fdu.Hypervisor == "cloud" {
			// Should recover a cloud FDU
			// only if it was never instantiated to K8s
			// because for replicas the K8s self-healing is always in place
		} else {
			if fimapi == nil {
				f.logger.Error("FIMAPI is nil with FDU of Kind FIM!!")
				entityRecord.Status = ERROR
				f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
				return
			}

			minReplicas := uint8(1)
			if fdu.Replicas != nil {
				minReplicas = *fdu.Replicas
			}

			instances := []string{}
			apiInstances, err := fimapi.FDU.InstanceList(*fdu.UUID, nil)
			if f.check(err) {
				entityRecord.Status = ERROR
				f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
				return
			}
			for _, v := range apiInstances {
				instances = append(instances, v...)
			}

			entityFDUInstances := []string{}
			intersection := intersect.Hash(instances, entityRecord.FDUs).([]interface{})
			for _, v := range intersection {
				entityFDUInstances = append(entityFDUInstances, fmt.Sprint(v))
			}

			f.logger.Info(fmt.Sprintf("Entity %s Instance %s FDU %s has %d/%d replicas", entityRecord.ID, entityRecord.UUID, *fdu.UUID, uint8(len(entityFDUInstances)), minReplicas))
			for minReplicas > uint8(len(entityFDUInstances)) {
				if uint8(len(entityFDUInstances)) == uint8(0) {
					//In this case we add first the descriptor
					fduFIMInterfaces := []fog05.FDUInterfaceDescriptor{}
					fduFIMConnectionPoints := []fog05.ConnectionPointDescriptor{}

					for _, intf := range fdu.Interfaces {
						vpci := ""
						if intf.VirtualInterface.Parent != nil {
							vpci = *intf.VirtualInterface.Parent
						}
						bw := 100
						if intf.VirtualInterface.Bandwidth != nil {
							bw = int(*intf.VirtualInterface.Bandwidth)
						}

						fimIntf := fog05.FDUInterfaceDescriptor{
							Name:          intf.Name,
							InterfaceType: fog05.INTERNAL,
							IsMGMT:        false,
							MACAddress:    intf.MACAddress,
							CPID:          intf.CPID,
							VirtualInterface: fog05.FDUVirtualInterface{
								InterfaceType: intf.VirtualInterface.InterfaceKind,
								VPCI:          vpci,
								Bandwidth:     bw,
							},
						}
						fduFIMInterfaces = append(fduFIMInterfaces, fimIntf)
					}

					for _, cp := range fdu.ConnectionPoints {

						vldID := ""
						for _, vl := range entityDescriptor.VirtualLinks {
							if vl.ID == cp.VLDRef {
								vldID = *vl.UUID
							}
						}
						if vldID == "" {
							f.logger.Info(fmt.Sprintf("EntityID: %s Virtual Link Reference %s is broken for FDU %s", entityRecord.ID, cp.VLDRef, *fdu.UUID))
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
							return
						}

						fimVLDRef, err := f.getFIMNetworkID(vldID, fimapi)
						if f.check(err) {
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
							return
						}

						fimCP := fog05.ConnectionPointDescriptor{
							UUID:   cp.UUID,
							ID:     cp.ID,
							Name:   cp.Name,
							VLDRef: &fimVLDRef,
						}

						fduFIMConnectionPoints = append(fduFIMConnectionPoints, fimCP)
					}

					fimFDU := fog05.FDU{
						ID:          fdu.ID,
						UUID:        fdu.UUID,
						Name:        fdu.Name,
						Description: fdu.Description,
						Image:       fdu.Image,
						Hypervisor:  fdu.Hypervisor,
						ComputationRequirements: fog05.FDUComputationalRequirements{
							CPUArch:         fdu.ComputationRequirements.CPUArch,
							CPUMinFrequency: fdu.ComputationRequirements.CPUMinFrequency,
							CPUMinCount:     fdu.ComputationRequirements.CPUMinCount,
							RAMSizeMB:       float64(fdu.ComputationRequirements.RAMSizeMB),
							StorageSizeGB:   float64(fdu.ComputationRequirements.StorageSizeMB) / 1024,
						},
						Storage:          []fog05.FDUStorageDescriptor{},
						MigrationKind:    "COLD",
						DependsOn:        fdu.DependsOn,
						IOPorts:          []fog05.FDUIOPort{},
						Interfaces:       fduFIMInterfaces,
						ConnectionPoints: fduFIMConnectionPoints,
					}

					f.logger.Info(fmt.Sprintf("EntityID: %s FDU: %s Storing in FIM %+v", entityRecord.ID, *fdu.UUID, fimFDU))
					_, err = fimapi.FDU.Onboard(fimFDU)
					if f.check(err) {
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						return
					}
				}

				fimFDU, err := fimapi.FDU.Info(*fdu.UUID)
				if err != nil {
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					return
				}

				//Finds a node for the FDU
				nodeid, err := f.findFIMNode(fimFDU, fimapi)
				if f.check(err) {
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					return
				}

				fimInstance, err := fimapi.FDU.Define(nodeid, *fimFDU.UUID)
				if f.check(err) {
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					return
				}

				instances = append(instances, fimInstance.UUID)

				_, err = fimapi.FDU.Configure(fimInstance.UUID)
				if f.check(err) {
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					return
				}
				_, err = fimapi.FDU.Start(fimInstance.UUID, nil)
				if f.check(err) {
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					return
				}
				fimInstance, err = fimapi.FDU.InstanceInfo(fimInstance.UUID)
				if f.check(err) {
					entityRecord.Status = ERROR
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					return
				}
				fduRecord := fog05.FOrcEFDURecord{
					UUID:   fimInstance.UUID,
					ID:     fimInstance.FDUID,
					Status: fimInstance.Status,
				}
				f.check(c.Orchestrator.AddFDURecord(fduRecord))
				entityFDUInstances = append(entityFDUInstances, fimInstance.UUID)
				entityRecord.FDUs = append(entityRecord.FDUs, fimInstance.UUID)
				f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
			}

			entityRecord.Status = STARTING
			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

		}
	}
}

func (f *FOrcE) monitoringWorker(qJob EnqueuedJob) {
	/*
	* This worker gets monitor information from one Entity Instance
	* It is added to the job queue periodically based on the instances
	* that are present in the system
	 */
	f.state.rwLock.Lock()
	defer f.state.rwLock.Unlock()

	f.logger.Info(fmt.Sprintf("Running Monitoring Job, JobID: %s", qJob.Job.JobID))
	if s, exists := f.state.connectors[qJob.systemid]; exists {
		if c, exists := s[qJob.tenantid]; exists {

			job := qJob.Job

			job.Status = RUNNING
			err := c.Orchestrator.AddJobInfo(job)
			f.check(err)

			//Getting the descriptor from the body
			info := EntityActionBody{}
			err = json.Unmarshal([]byte(job.Body), &info)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			entityRecord, err := c.Orchestrator.FindEntityInstanceInfo(info.UUID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			entityID := entityRecord.ID
			entityDescriptor, err := c.Orchestrator.GetEntityInfo(entityID)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			ready := true

			if entityRecord.Status == RECOVERING {
				f.logger.Info(fmt.Sprintf("JobID: %s Instance %s is recovering ", qJob.Job.JobID, entityRecord.UUID))
				job.Status = "completed"
				err = c.Orchestrator.AddJobInfo(job)
				f.check(err)
				f.logger.Info(fmt.Sprintf("Monitoring Job: %s done", qJob.Job.JobID))
				return
			}

			// if entityRecord.Status == ERROR {
			// 	f.logger.Info(fmt.Sprintf("JobID: %s Instance %s is error!! Will not recover!!", qJob.Job.JobID, entityRecord.UUID))
			// 	job.Status = "completed"
			// 	err = c.Orchestrator.AddJobInfo(job)
			// 	f.check(err)
			// 	f.logger.Info(fmt.Sprintf("Monitoring Job: %s done", qJob.Job.JobID))
			// 	return
			// }

			for _, fdu := range entityDescriptor.FDUs {

				if fdu.Hypervisor == "cloud" {
					clientset, exists := f.state.clouds[qJob.systemid][qJob.tenantid][*entityRecord.CloudID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s Cloud %s not exists", qJob.Job.JobID, *entityRecord.CloudID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						return
					}

					deploymentsClient := clientset.AppsV1().Deployments(apiv1.NamespaceDefault)

					deployment := &appsv1.Deployment{}
					depDesc, err := base64.StdEncoding.DecodeString(*fdu.HypervisorSpecific)
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						return
					}
					dec := yaml.NewYAMLOrJSONDecoder(bytes.NewReader(depDesc), 65535)
					err = dec.Decode(&deployment)
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						return
					}
					f.logger.Info(fmt.Sprintf("JobID: %s Deployment %+v", qJob.Job.JobID, deployment))

					orchInstances, err := c.Orchestrator.GetAllFDURecordsInfo(*fdu.UUID)
					if f.check(err) {
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						return
					}
					allInstances := []string{}
					entityFDUInstances := []string{}
					for _, record := range orchInstances {
						allInstances = append(allInstances, record.UUID)

					}
					intersection := intersect.Hash(allInstances, entityRecord.FDUs).([]interface{})
					for _, v := range intersection {
						entityFDUInstances = append(entityFDUInstances, fmt.Sprint(v))
					}

					for _, inst := range entityFDUInstances {

						depInstance, err := deploymentsClient.Get(context.TODO(), inst, metav1.GetOptions{})
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							entityRecord.Status = ERROR
							f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
							return
						}
						if depInstance.Status.AvailableReplicas == *deployment.Spec.Replicas {
							ready = ready && true
							fduRecord := fog05.FOrcEFDURecord{
								UUID:   inst,
								ID:     *fdu.UUID,
								Status: "run",
							}
							f.check(c.Orchestrator.AddFDURecord(fduRecord))
							// from Cloud not recovering is needed, K8s uses its own self-healing for PODs
						} else {
							ready = false
						}

					}

				} else {

					fimapi, exists := f.state.fims[qJob.systemid][qJob.tenantid][*entityRecord.FIMID]
					if !exists {
						f.logger.Info(fmt.Sprintf("JobID: %s FIM %s not exists", qJob.Job.JobID, *entityRecord.FIMID))
						job.Status = "failed"
						err := c.Orchestrator.AddJobInfo(job)
						f.check(err)
						return
					}
					minReplicas := uint8(1)
					if fdu.Replicas != nil {
						minReplicas = *fdu.Replicas
					}
					// if fdu.ScalingPolicies != nil {
					// 	for _, sp := range *fdu.ScalingPolicies {
					// 		if sp.MinReplicas > minReplicas {
					// 			minReplicas = sp.MinReplicas
					// 		}
					// 	}
					// }

					// instances := []string{}
					// apiInstances, err := fimapi.FDU.InstanceList(*fdu.UUID, nil)
					// if f.check(err) {
					// 	job.Status = "failed"
					// 	err := c.Orchestrator.AddJobInfo(job)
					// 	f.check(err)
					// 	return
					// }
					// for _, v := range apiInstances {
					// 	instances = append(instances, v...)
					// }

					// entityFDUInstances := []string{}
					// intersection := intersect.Hash(instances, entityRecord.FDUs).([]interface{})
					// for _, v := range intersection {
					// 	entityFDUInstances = append(entityFDUInstances, fmt.Sprint(v))
					// }

					// if minReplicas > uint8(len(entityFDUInstances)) {
					// 	f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s Entity: %s FDU: %s has less replicas than needed", qJob.Job.JobID, entityRecord.UUID, entityRecord.ID, *fdu.UUID))
					// 	entityRecord.Status = ERROR
					// 	f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
					// 	ready = false
					// 	// we should trigger here the new replicas
					// 	//Getting also cloud API if present
					// 	if entityRecord.CloudID != nil {
					// 		cloud, _ := f.state.clouds[qJob.systemid][qJob.tenantid][*entityRecord.CloudID]
					// 		go f.recoverWorker(entityRecord, fimapi, cloud, c)
					// 	} else {
					// 		go f.recoverWorker(entityRecord, fimapi, nil, c)
					// 	}

					// }

					notWorkingInstances := []string{}

					for _, instanceID := range entityRecord.FDUs {
						fduInstanceInfo, err := fimapi.FDU.InstanceInfo(instanceID)
						if f.check(err) {
							f.logger.Error(fmt.Sprintf("JobID: %s Instance: %s Entity: %s FDU: %s FDU Instance: %s is not there...", qJob.Job.JobID, entityRecord.UUID, entityRecord.ID, *fdu.UUID, instanceID))
							ready = false
							entityRecord.Status = ERROR
							notWorkingInstances = append(notWorkingInstances, instanceID)
						} else {
							f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s Entity: %s FDU: %s FDU Instance: %s Status: %s", qJob.Job.JobID, entityRecord.UUID, entityRecord.ID, *fdu.UUID, instanceID, fduInstanceInfo.Status))
							switch fduInstanceInfo.Status {
							case "RUN":
								ready = ready && true
							case "STARTING", "CONFIGURE", "DEFINE":
								ready = false
							case "ERROR", "PAUSE":
								ready = false
								entityRecord.Status = ERROR
								notWorkingInstances = append(notWorkingInstances, instanceID)
							default:
								ready = false
							}

							fduRecord := fog05.FOrcEFDURecord{
								UUID:   fduInstanceInfo.UUID,
								ID:     fduInstanceInfo.FDUID,
								Status: fduInstanceInfo.Status,
							}
							f.check(c.Orchestrator.AddFDURecord(fduRecord))
						}

					}
					f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s Removing %+v from %+v", qJob.Job.JobID, entityRecord.UUID, notWorkingInstances, entityRecord.FDUs))
					for i := 0; i < len(entityRecord.FDUs); i++ {
						id := entityRecord.FDUs[i]
						for _, rem := range notWorkingInstances {
							if id == rem {
								entityRecord.FDUs = append(entityRecord.FDUs[:i], entityRecord.FDUs[i+1:]...)
								i--
								break
							}
						}
					}
					f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

					f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s FDUs %+v", qJob.Job.JobID, entityRecord.UUID, entityRecord.FDUs))
					if minReplicas > uint8(len(entityRecord.FDUs)) {
						f.logger.Info(fmt.Sprintf("JobID: %s Instance: %s Entity: %s FDU: %s has less replicas than needed", qJob.Job.JobID, entityRecord.UUID, entityRecord.ID, *fdu.UUID))
						entityRecord.Status = ERROR
						f.check(c.Orchestrator.AddEntityRecord(*entityRecord))
						ready = false
						// we should trigger here the new replicas
						//Getting also cloud API if present
						if entityRecord.CloudID != nil {
							cloud, _ := f.state.clouds[qJob.systemid][qJob.tenantid][*entityRecord.CloudID]
							go f.recoverWorker(entityRecord, fimapi, cloud, c)
						} else {
							go f.recoverWorker(entityRecord, fimapi, nil, c)
						}

						v, err := json.Marshal(entityRecord)
						if f.check(err) {
							job.Status = "failed"
							err := c.Orchestrator.AddJobInfo(job)
							f.check(err)
							return
						}
						job.Status = "completed"
						job.Body = string(v)
						err = c.Orchestrator.AddJobInfo(job)
						f.check(err)

						f.logger.Info(fmt.Sprintf("Monitoring Job: %s done", qJob.Job.JobID))
						return

					}
				}

			}

			if ready {
				//Storing record in Orchestrator catalog
				entityRecord.Status = RUNNING

			}

			f.check(c.Orchestrator.AddEntityRecord(*entityRecord))

			v, err := json.Marshal(entityRecord)
			if f.check(err) {
				job.Status = "failed"
				err := c.Orchestrator.AddJobInfo(job)
				f.check(err)
				return
			}

			job.Status = "completed"
			job.Body = string(v)
			err = c.Orchestrator.AddJobInfo(job)
			f.check(err)

			f.logger.Info(fmt.Sprintf("Monitoring Job: %s done", qJob.Job.JobID))
			return
		}
		f.logger.Error(fmt.Sprintf("Job %s scheduled on tenant %s that does not exists!", qJob.Job.JobID, qJob.tenantid))
		return
	}
	f.logger.Error(fmt.Sprintf("Job %s scheduled on system %s that does not exists!", qJob.Job.JobID, qJob.systemid))
	return
}

// Entity Descriptors

//GetEntities gets all the available entities in the given system+tenant (catalog)
func (f *FOrcE) GetEntities(sysid string, tenantid string) ([]string, error) {
	entities := []string{}
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			rawEntities, err := c.Orchestrator.GetAllEntitiesInfo()
			if f.check(err) {
				return entities, err
			}
			for _, e := range rawEntities {
				entities = append(entities, *e.UUID)
			}
			return entities, nil

		}
		return entities, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return entities, fmt.Errorf("System %s does not exists", sysid)
}

//GetEntity gets information about the given entity from the catalog
func (f *FOrcE) GetEntity(sysid string, tenantid string, entityid string) (*fog05.EntityDescriptor, error) {
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			info, err := c.Orchestrator.GetEntityInfo(entityid)
			if f.check(err) {
				return nil, err
			}
			return info, nil

		}
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return nil, fmt.Errorf("System %s does not exists", sysid)
}

//AddEntity adds the given entity to the given system+tenant catalog
func (f *FOrcE) AddEntity(sysid string, tenantid string, data fog05.EntityDescriptor) error {
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {

			for _, fdu := range data.FDUs {
				err := c.Orchestrator.AddFDUInfo(fdu)
				if f.check(err) {
					return err
				}

			}

			for _, vl := range data.VirtualLinks {
				err := c.Orchestrator.AddVirtualLinkInfo(vl)
				if f.check(err) {
					return err
				}
			}

			err := c.Orchestrator.AddEntityInfo(data)
			if f.check(err) {
				return err
			}

			return nil

		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//RemoveEntity removes the given entity to the given system+tenant catalog
func (f *FOrcE) RemoveEntity(sysid string, tenantid string, entityid string) error {

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			err := c.Orchestrator.RemoveEntityInfo(entityid)
			if f.check(err) {
				return err
			}
			return nil

		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

// Entity Records

//GetEntityInstances gets all the available entities instances in the given system+tenant (catalog)
func (f *FOrcE) GetEntityInstances(sysid string, tenantid string, entityid string) ([]string, error) {

	instances := []string{}
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			rawInstances, err := c.Orchestrator.GetAllEntityRecordsInfo(entityid)
			if f.check(err) {
				return instances, err
			}
			for _, i := range rawInstances {
				instances = append(instances, i.UUID)
			}
			return instances, nil

		}
		return instances, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return instances, fmt.Errorf("System %s does not exists", sysid)
}

//GetEntityInstance gets information about the given entity instance from the catalog
func (f *FOrcE) GetEntityInstance(sysid string, tenantid string, entityid string, instanceid string) (*fog05.EntityRecord, error) {

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			info, err := c.Orchestrator.GetEntityInstanceInfo(entityid, instanceid)
			if f.check(err) {
				return nil, err
			}
			return info, nil

		}
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return nil, fmt.Errorf("System %s does not exists", sysid)
}

//FindEntityInstance gets information about the given entity instance from the catalog
func (f *FOrcE) FindEntityInstance(sysid string, tenantid string, instanceid string) (*fog05.EntityRecord, error) {

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			info, err := c.Orchestrator.FindEntityInstanceInfo(instanceid)
			if f.check(err) {
				return nil, err
			}
			return info, nil

		}
		return nil, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return nil, fmt.Errorf("System %s does not exists", sysid)
}

//GetInstances gets information about the instances running in the system
func (f *FOrcE) GetInstances(sysid string, tenantid string) ([]string, error) {

	instances := []string{}
	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			infos, err := c.Orchestrator.GetAllEntityRecordsInfo("*")
			if f.check(err) {
				return instances, err
			}
			for _, info := range infos {
				instances = append(instances, info.UUID)
			}
			return instances, nil

		}
		return instances, fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return instances, fmt.Errorf("System %s does not exists", sysid)
}

//AddEntityInstance adds the given entity instance to the given system+tenant catalog
func (f *FOrcE) AddEntityInstance(sysid string, tenantid string, data fog05.EntityRecord) error {

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			err := c.Orchestrator.AddEntityRecord(data)
			if f.check(err) {
				return err
			}
			return nil

		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//RemoveEntityInstance removes the given entity instance to the given system+tenant catalog
func (f *FOrcE) RemoveEntityInstance(sysid string, tenantid string, entityid string, instanceid string) error {

	if s, exists := f.state.connectors[sysid]; exists {
		if c, exists := s[tenantid]; exists {
			err := c.Orchestrator.RemoveEntityRecord(entityid, instanceid)
			if f.check(err) {
				return err
			}
			return nil

		}
		return fmt.Errorf("Tenant %s does not exists", tenantid)
	}
	return fmt.Errorf("System %s does not exists", sysid)
}

//Utility

func (f *FOrcE) monitoringJobsSpawner(c *fog05.FOrcEZConnector, sysid string, tenantid string, id string, fimID *string, cloudID *string) {
	for {
		time.Sleep(10 * time.Second)
		eRecord, err := c.Orchestrator.FindEntityInstanceInfo(id)
		if f.check(err) {
			f.logger.Info(fmt.Sprintf("Ending monitoring spawner for %s", id))
			return
		}
		if eRecord.Status == OFFLOADED {
			f.logger.Info(fmt.Sprintf("Ending monitoring spawner for %s", id))
			return
		}
		body := EntityActionBody{
			UUID:    id,
			FIMID:   fimID,
			CloudID: cloudID,
		}
		v, _ := json.Marshal(body)
		jobR := fog05.RequestNewJobMessage{
			Sender:  "monitoringJobsSpawner",
			JobKind: "monitoring",
			Body:    string(v),
		}
		_, err = f.InsertNewJob(sysid, tenantid, jobR)
		if f.check(err) {
			f.logger.Info(fmt.Sprintf("Unable to add monitoring job for %s to queue error: %s", id, err.Error()))
		} else {
			f.logger.Info(fmt.Sprintf("Added monitoring job for %s", id))
		}

	}
}

func (f *FOrcE) findFDUForInstance(c *fog05.FOrcEZConnector, instanceid string) (*fog05.FOrcEFDUDescriptor, error) {

	fdus, err := c.Orchestrator.GetAllFDUsInfo()
	if f.check(err) {
		return nil, err
	}

	for _, d := range fdus {
		instances, err := c.Orchestrator.GetAllFDURecordsInfo(*d.UUID)
		if f.check(err) {
			return nil, err
		}
		for _, i := range instances {
			if i.UUID == instanceid {
				return &d, nil
			}
		}
	}
	return nil, fmt.Errorf("Unable to find FDU for instance %s", instanceid)

}

func (f *FOrcE) findIndex(id string, list []fog05.FOrcEFDUDescriptor) int {
	for p, v := range list {
		if id == v.ID {
			return p
		}
	}
	return -1
}

func (f *FOrcE) orderFDUs(fdus []fog05.FOrcEFDUDescriptor) []fog05.FOrcEFDUDescriptor {

	ordered := []fog05.FOrcEFDUDescriptor{}

	for len(ordered) < len(fdus) {
		for i := 0; i < len(fdus); i++ {
			fdu := &fdus[i]
			if len(fdu.DependsOn) > 0 {
				found := true
				for _, dep := range fdu.DependsOn {

					if index := f.findIndex(dep, ordered); index != -1 {
						found = found && true
					} else {
						found = false
					}
				}
				if found {
					if exists := f.findIndex(fdu.ID, ordered); exists == -1 {
						ordered = append(ordered, *fdu)
					}
				}
			} else {
				if exists := f.findIndex(fdu.ID, ordered); exists == -1 {
					ordered = append(ordered, *fdu)
				}
			}
		}
	}
	return ordered
}

func (f *FOrcE) findFIMNode(fdu *fog05.FDU, fimapi *fim.FIMAPI) (string, error) {
	//Check nodes compatibility by "multicast" asking to nodes if they are compatible
	nodes, err := fimapi.FDU.GetCompatibleNodes(*fdu.UUID)
	if f.check(err) {
		return "", err
	}
	if len(nodes) == 0 {
		return "", fmt.Errorf("No node found for this FDU: %+v", fdu)
	}
	f.logger.Info(fmt.Sprintf("Compatible nodes for %s are %+v", *fdu.UUID, nodes))
	//Should select the actual node
	// - Random
	// - First Fit
	// - Least Used

	//Using random selection
	randomIndex := rand.Intn(len(nodes))
	pick := nodes[randomIndex]
	f.logger.Info(fmt.Sprintf("Random pick for %s is node: %s", *fdu.UUID, pick))
	return pick, nil

}

func (f *FOrcE) getFIMNetworkID(id string, fimapi *fim.FIMAPI) (string, error) {
	nets, err := fimapi.Network.List()
	if f.check(err) {
		return "", err
	}
	// f.logger.Info(fmt.Sprintf("FIM Networks %+v", nets))
	for _, nid := range nets {
		netInfo, err := fimapi.Network.GetNetwork(nid)
		if f.check(err) {
			return "", err
		}
		// f.logger.Info(fmt.Sprintf("Checking %+v; %s == %s ? %t", netInfo, netInfo.Name, id, netInfo.Name == id))
		if netInfo.Name == id {
			return netInfo.UUID, nil
		}
	}

	return "", fmt.Errorf("Virtual Network %s does not exists", id)
}

func (f *FOrcE) getFIMNetworkIDs(id string, fimapi *fim.FIMAPI) ([]string, error) {
	fimNets := []string{}

	nets, err := fimapi.Network.List()
	if f.check(err) {
		return fimNets, err
	}
	// f.logger.Info(fmt.Sprintf("FIM Networks %+v", nets))
	for _, nid := range nets {
		netInfo, err := fimapi.Network.GetNetwork(nid)
		if f.check(err) {
			return fimNets, err
		}
		// f.logger.Info(fmt.Sprintf("Checking %+v; %s == %s ? %t", netInfo, netInfo.Name, id, netInfo.Name == id))
		if netInfo.Name == id {
			fimNets = append(fimNets, netInfo.UUID)
		}
	}

	return fimNets, nil
}
