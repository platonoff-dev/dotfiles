package main

import (
	"fmt"
	"os"
	"strings"
)

func main() {
	folder := os.Args[1]
	files, err := os.ReadDir(folder)
	if err != nil {
		panic(err)
	}

	filesPaths := []string{}
	for _, file := range files {
		if file.IsDir() {
			continue
		}

		filePath := folder + "/" + file.Name()
		filesPaths = append(filesPaths, filePath)
	}

	fmt.Println(strings.Join(filesPaths, ":"))
}
