package main

import (
	"flag"
	"os"
	"slices"
	"strings"

	"gopkg.in/yaml.v2"
)

func main() {
	configsDir := os.Args[1]

	configFiles, err := os.ReadDir(configsDir)
	if err != nil {
		panic(err)
	}

	ignoreFilesArg := flag.String("ignore", "", "Comma separated list of files to ignore")

	var ignoreFiles []string
	if ignoreFilesArg != nil {
		ignoreFiles = strings.Split(*ignoreFilesArg, ",")
	}

	for _, configFile := range configFiles {
		if configFile.IsDir() || slices.Contains(ignoreFiles, configFile.Name()) {
			continue
		}
		filePath := configsDir + "/" + configFile.Name()
		content, err := os.ReadFile(filePath)
		if err != nil {
			panic(err)
		}

		var config map[string]interface{}
		if err := yaml.Unmarshal(content, &config); err != nil {
			panic(err)
		}

		contexts := config["contexts"].([]interface{})
		context := contexts[0].(map[interface{}]interface{})
		contextName := context["name"].(string)
		contextContext := context["context"].(map[interface{}]interface{})

		users := config["users"].([]interface{})
		user := users[0].(map[interface{}]interface{})
		prefixedUser := contextName + "-" + user["name"].(string)

		if strings.HasPrefix(user["name"].(string), contextName) {
			continue
		}

		user["name"] = prefixedUser
		contextContext["user"] = prefixedUser

		content, err = yaml.Marshal(config)
		if err != nil {
			panic(err)
		}

		err = os.WriteFile(filePath, content, os.ModePerm)
		if err != nil {
			panic(err)
		}

		println("Updated kubeconfig file: " + configFile.Name())
	}
}
