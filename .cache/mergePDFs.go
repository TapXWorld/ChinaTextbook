package main

import (
	"io/ioutil"
	"os"
	"sort"
	"strings"
)

func main() {
	dirPath := "." // 当前目录
	mergeSplitPDFsInDirectory(dirPath)
}

func mergeSplitPDFsInDirectory(dirPath string) {
	files, err := ioutil.ReadDir(dirPath)
	if err != nil {
		panic(err)
	}

	splitFiles := make(map[string][]string)

	for _, file := range files {
		if file.IsDir() {
			continue
		}
		fileName := file.Name()
		if strings.Contains(fileName, ".pdf.") {
			baseName := strings.Split(fileName, ".pdf.")[0] + ".pdf"
			splitFiles[baseName] = append(splitFiles[baseName], fileName)
		}
	}

	for baseName, parts := range splitFiles {
		sort.Strings(parts) // 确保文件顺序正确
		mergeFiles(baseName, parts)
	}
}

func mergeFiles(baseName string, parts []string) {
	mergedFile, err := os.Create(baseName)
	if err != nil {
		panic(err)
	}
	defer mergedFile.Close()

	for _, part := range parts {
		data, err := ioutil.ReadFile(part)
		if err != nil {
			panic(err)
		}
		_, err = mergedFile.Write(data)
		if err != nil {
			panic(err)
		}
		os.Remove(part) // 合并后删除分割文件
	}
}
