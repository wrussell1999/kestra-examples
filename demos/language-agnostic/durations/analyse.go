package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"regexp"
	"strconv"
)

type TaskState struct {
	Duration string `json:"duration"`
}

type TaskRun struct {
	TaskId string    `json:"taskId"`
	State  TaskState `json:"state"`
}

type Execution struct {
	TaskRunList []TaskRun `json:"taskRunList"`
}

type Root struct {
	Results []Execution `json:"results"`
}

func parseISODuration(iso string) float64 {
	re := regexp.MustCompile(`PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?`)
	matches := re.FindStringSubmatch(iso)

	if matches == nil {
		return 0
	}

	hours, _ := strconv.ParseFloat(matches[1], 64)
	minutes, _ := strconv.ParseFloat(matches[2], 64)
	seconds, _ := strconv.ParseFloat(matches[3], 64)

	return hours*3600 + minutes*60 + seconds
}

func main() {
	data, err := ioutil.ReadFile("make_data.json")
	if err != nil {
		fmt.Println("Error reading file:", err)
		os.Exit(1)
	}

	var root Root
	if err := json.Unmarshal(data, &root); err != nil {
		fmt.Println("Error parsing JSON:", err)
		os.Exit(1)
	}

	var total float64
	var count int

	for _, exec := range root.Results {
		for _, task := range exec.TaskRunList {
			if task.TaskId == "python" {
				duration := parseISODuration(task.State.Duration)
				if duration > 0 {
					total += duration
					count++
				}
			}
		}
	}

	if count > 0 {
		avg := total / float64(count)
		fmt.Printf("Average duration for 'transform' task: %.6f seconds\n", avg)
	} else {
		fmt.Println("No 'transform' task durations found.")
	}
}
