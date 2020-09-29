package main

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"

	fog05 "github.com/eclipse-fog05/sdk-go/fog05sdk"
	"github.com/gorilla/mux"
	log "github.com/sirupsen/logrus"
)

const UUIDREGEX string = "[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}"

type Configuration struct {
	Address string `json:"address"` //address where listening
	Port    string `json:"port"`    //port where listening
	Zenoh   string `json:"zenoh"`   //zenoh locator
}

type App struct {
	force  *FOrcE
	router *mux.Router
	conf   Configuration
	logger *log.Logger
}

func NewApp(conf Configuration) (*App, error) {

	f, err := NewFOrcE(conf.Zenoh)
	if err != nil {
		return nil, err
	}
	r := mux.NewRouter()
	a := App{
		force:  f,
		router: r,
		conf:   conf,
		logger: log.New(),
	}
	return &a, nil

}

func (a *App) Initialize() {
	err := a.force.Init()
	if a.check(err) {
		panic(err)
	}
	a.initializeRoutes()
	a.force.Start()
}

func (a *App) Run() {
	a.logger.Info(fmt.Sprintf("Listening on %s:%s", a.conf.Address, a.conf.Port))
	a.logger.Fatal(http.ListenAndServe(fmt.Sprintf("%s:%s", a.conf.Address, a.conf.Port), a.router))
}

func (a *App) initializeRoutes() {
	// o.router.HandleFunc("/products", a.getProducts).Methods("GET")
	a.router.HandleFunc("/system", a.addSystem).Methods("POST")
	a.router.HandleFunc("/system", a.getSystems).Methods("GET")
	a.router.HandleFunc("/system/{id:"+UUIDREGEX+"}", a.deleteSystem).Methods("DELETE")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}", a.getTenants).Methods("GET")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant", a.addTenant).Methods("POST")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{id:"+UUIDREGEX+"}", a.deleteTenant).Methods("DELETE")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{id:"+UUIDREGEX+"}/job", a.addJob).Methods("POST")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/job/{id:"+UUIDREGEX+"}", a.getJob).Methods("GET")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{id:"+UUIDREGEX+"}/entity", a.getEntities).Methods("GET")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/entity/{id:"+UUIDREGEX+"}", a.getEntity).Methods("GET")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/instances/{id:"+UUIDREGEX+"}", a.getEntityInstance).Methods("GET")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/instances", a.getEntityInstance).Methods("GET")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/fim", a.addFIM).Methods("POST")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/fim", a.getFIMs).Methods("GET")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/fim/{id:"+UUIDREGEX+"}", a.deleteFIM).Methods("DELETE")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/fim/{id:"+UUIDREGEX+"}", a.getFIM).Methods("GET")

	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/cloud", a.addCloud).Methods("POST")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/cloud", a.getClouds).Methods("GET")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/cloud/{id:"+UUIDREGEX+"}", a.deleteCloud).Methods("DELETE")
	a.router.HandleFunc("/system/{sys-id:"+UUIDREGEX+"}/tenant/{tenant-id:"+UUIDREGEX+"}/cloud/{id:"+UUIDREGEX+"}", a.getCloud).Methods("GET")
}

func (a *App) addSystem(w http.ResponseWriter, r *http.Request) {
	sysid := r.FormValue("id")
	exists := len(sysid) > 0
	a.logger.Info(fmt.Sprintf("Called addSystem with %s", sysid))
	if exists {
		err := a.force.AddSystem(sysid)
		if a.check(err) {
			respondWithError(w, http.StatusBadRequest, err.Error())
			return
		}
		respondWithOk(w, http.StatusOK)
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing id parameter")
}

func (a *App) getSystems(w http.ResponseWriter, r *http.Request) {
	a.logger.Info("Called getSystems")
	systems := a.force.GetSystems()
	resp := map[string]interface{}{
		"systems": systems,
	}
	respondWithJSON(w, http.StatusOK, resp)
}

func (a *App) deleteSystem(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called deleteSystem with  %+v", vars))

	if sysid, exists := vars["id"]; exists {
		err := a.force.RemoveSystem(sysid)
		if a.check(err) {
			respondWithError(w, http.StatusBadRequest, err.Error())
			return
		}
		respondWithOk(w, http.StatusOK)
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing id parameter")
}

func (a *App) addTenant(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called addTenant with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		tenantid := r.FormValue("id")
		exists := len(sysid) > 0
		if exists {
			err := a.force.AddTenant(sysid, tenantid)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
				return
			}
			respondWithOk(w, http.StatusOK)
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing id parameter")
	}
}

func (a *App) getTenants(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getTenants with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		tenants, err := a.force.GetTenants(sysid)
		if a.check(err) {
			respondWithError(w, http.StatusBadRequest, err.Error())
			return
		}
		resp := map[string]interface{}{
			"system":  sysid,
			"tenants": tenants,
		}
		respondWithJSON(w, http.StatusOK, resp)
	}

}

func (a *App) deleteTenant(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called deleteTenant with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["id"]; exists {
			err := a.force.RemoveTenant(sysid, tenantid)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
				return
			}
			respondWithOk(w, http.StatusOK)
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing id parameter")
	}
}

func (a *App) addFIM(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	fimid := r.FormValue("id")
	locator := r.FormValue("locator")
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			a.logger.Info(fmt.Sprintf("Called addFIM with %s %s", fimid, locator))
			if len(fimid) > 0 && len(locator) > 0 {
				err := a.force.AddFIM(sysid, tenantid, fimid, locator)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				respondWithOk(w, http.StatusOK)
				return
			}
		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing parameter")
	return
}

func (a *App) getFIM(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getFIM with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if fimid, exists := vars["id"]; exists {
				fim, err := a.force.GetFIM(sysid, tenantid, fimid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				resp := map[string]interface{}{
					"system": sysid,
					"tenant": tenantid,
					"fim":    fim,
				}
				respondWithJSON(w, http.StatusOK, resp)
				return
				respondWithOk(w, http.StatusOK)
				return
			}
			respondWithError(w, http.StatusBadRequest, "missing id parameter")
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing tenant-id parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing sys-id parameter")
	return
}

func (a *App) getFIMs(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info("Called getFIMs")
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			systems, err := a.force.GetFIMs(sysid, tenantid)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
			}
			resp := map[string]interface{}{
				"system": sysid,
				"tenant": tenantid,
				"fims":   systems,
			}
			respondWithJSON(w, http.StatusOK, resp)
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing parameter")
	return
}

func (a *App) deleteFIM(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called deleteFIM with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if fimid, exists := vars["id"]; exists {
				err := a.force.RemoveFIM(sysid, tenantid, fimid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				respondWithOk(w, http.StatusOK)
				return
			}
			respondWithError(w, http.StatusBadRequest, "missing id parameter")
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing tenant-id parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing sys-id parameter")
	return
}

func (a *App) addCloud(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	cloudid := r.FormValue("id")
	cloudConfig := r.FormValue("config")
	ca, err := base64.StdEncoding.DecodeString(r.FormValue("ca"))
	if a.check(err) {
		respondWithError(w, http.StatusBadRequest, err.Error())
		return
	}
	cert, err := base64.StdEncoding.DecodeString(r.FormValue("cert"))
	if a.check(err) {
		respondWithError(w, http.StatusBadRequest, err.Error())
		return
	}
	key, err := base64.StdEncoding.DecodeString(r.FormValue("key"))
	if a.check(err) {
		respondWithError(w, http.StatusBadRequest, err.Error())
		return
	}
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if len(cloudid) > 0 && len(cloudid) > 0 && len(ca) > 0 && len(cert) > 0 && len(key) > 0 {
				a.logger.Info(fmt.Sprintf("Called addCloud with %s %s", cloudid, cloudConfig))
				err := a.force.AddCloud(sysid, tenantid, cloudid, cloudConfig, ca, cert, key)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				respondWithOk(w, http.StatusOK)
				return
			}
		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing parameter")
	return
}

func (a *App) getClouds(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info("Called getClouds")
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			systems, err := a.force.GetClouds(sysid, tenantid)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
			}
			resp := map[string]interface{}{
				"system": sysid,
				"tenant": tenantid,
				"clouds": systems,
			}
			respondWithJSON(w, http.StatusOK, resp)
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing parameter")
	return
}

func (a *App) getCloud(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getCloud with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if fimid, exists := vars["id"]; exists {
				cloud, err := a.force.GetCloud(sysid, tenantid, fimid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				resp := map[string]interface{}{
					"system": sysid,
					"tenant": tenantid,
					"cloud":  cloud,
				}
				respondWithJSON(w, http.StatusOK, resp)
				return
			}
			respondWithError(w, http.StatusBadRequest, "missing id parameter")
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing tenant-id parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing sys-id parameter")
	return
}

func (a *App) deleteCloud(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called deleteCloud with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if fimid, exists := vars["id"]; exists {
				err := a.force.RemoveCloud(sysid, tenantid, fimid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				respondWithOk(w, http.StatusOK)
				return
			}
			respondWithError(w, http.StatusBadRequest, "missing id parameter")
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing tenant-id parameter")
		return
	}
	respondWithError(w, http.StatusBadRequest, "missing sys-id parameter")
	return
}

func (a *App) addJob(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	defer r.Body.Close()
	body, err := ioutil.ReadAll(r.Body)
	if a.check(err) {
		respondWithError(w, http.StatusBadRequest, err.Error())
		return
	}
	a.logger.Info(fmt.Sprintf("Called addJob with %+v body: %s", vars, body))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["id"]; exists {
			// decoder := json.NewDecoder(r.Body)

			var j fog05.RequestNewJobMessage
			err = json.Unmarshal(body, &j)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
				return
			}
			reply, err := a.force.InsertNewJob(sysid, tenantid, j)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
				return
			}
			respondWithJSON(w, http.StatusOK, reply)
			return

		}
		respondWithError(w, http.StatusBadRequest, "missing id parameter")
	}
}

func (a *App) getJob(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getJob with  %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if jid, exists := vars["id"]; exists {
				reply, err := a.force.GetJob(sysid, tenantid, jid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				respondWithJSON(w, http.StatusOK, reply)
				return
			}
		}
	}
}

func (a *App) getEntities(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getEntities with %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["id"]; exists {

			entities, err := a.force.GetEntities(sysid, tenantid)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
				return
			}
			reply := map[string]interface{}{
				"system":   sysid,
				"tenant":   tenantid,
				"entities": entities,
			}
			respondWithJSON(w, http.StatusOK, reply)
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing id parameter")
	}
}

func (a *App) getEntity(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getEntities with %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if entityid, exists := vars["id"]; exists {
				entity, err := a.force.GetEntity(sysid, tenantid, entityid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}
				reply := map[string]interface{}{
					"system": sysid,
					"tenant": tenantid,
					"entity": entity,
				}
				respondWithJSON(w, http.StatusOK, reply)
				return
			}
			respondWithError(w, http.StatusBadRequest, "missing parameter")
			return

		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
	}
}

func (a *App) getEntityInstances(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getEntityInstances with %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			instances, err := a.force.GetInstances(sysid, tenantid)
			if a.check(err) {
				respondWithError(w, http.StatusBadRequest, err.Error())
				return
			}

			reply := map[string]interface{}{
				"system":    sysid,
				"tenant":    tenantid,
				"instances": instances,
			}
			respondWithJSON(w, http.StatusOK, reply)
			return
		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
		return

	}
	respondWithError(w, http.StatusBadRequest, "missing parameter")
}

func (a *App) getEntityInstance(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	a.logger.Info(fmt.Sprintf("Called getEntityInstance with %+v", vars))
	if sysid, exists := vars["sys-id"]; exists {
		if tenantid, exists := vars["tenant-id"]; exists {
			if instanceid, exists := vars["id"]; exists {
				instance, err := a.force.FindEntityInstance(sysid, tenantid, instanceid)
				if a.check(err) {
					respondWithError(w, http.StatusBadRequest, err.Error())
					return
				}

				reply := map[string]interface{}{
					"system":   sysid,
					"tenant":   tenantid,
					"entity":   instance.ID,
					"instance": instance,
				}
				respondWithJSON(w, http.StatusOK, reply)
				return
			}
			respondWithError(w, http.StatusBadRequest, "missing parameter")
			return

		}
		respondWithError(w, http.StatusBadRequest, "missing parameter")
	}
}

func (a *App) check(err error) bool {
	if err != nil {
		fun, line := MyCaller()
		a.logger.Error(fmt.Sprintf("App Error Check got: %s Called by %s:%d", err.Error(), fun, line))
		return true
	}
	return false
}

func respondWithError(w http.ResponseWriter, code int, message string) {
	respondWithJSON(w, code, map[string]string{"error": message})
}

func respondWithJSON(w http.ResponseWriter, code int, payload interface{}) {
	response, _ := json.Marshal(payload)

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	w.Write(response)
}

func respondWithOk(w http.ResponseWriter, code int) {
	respondWithJSON(w, code, map[string]string{"ok": "done"})
}
