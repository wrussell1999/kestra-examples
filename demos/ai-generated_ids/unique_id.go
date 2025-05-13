package main

import (
	"crypto/md5"
	"encoding/csv"
	"encoding/hex"
	"fmt"
	"os"
)

func main() {
	inputFile := "green_tripdata_2019-01.csv"
	outputFile := "your_output_file_with_hashes.csv"

	// Open the input CSV file
	f, err := os.Open(inputFile)
	if err != nil {
		panic(err)
	}
	defer f.Close()

	r := csv.NewReader(f)
	records, err := r.ReadAll()
	if err != nil {
		panic(err)
	}

	if len(records) < 1 {
		fmt.Println("Empty CSV file")
		return
	}

	// Identify header indexes
	header := records[0]
	header = append(header, "unique_row_id")

	colIdx := map[string]int{}
	for i, col := range records[0] {
		colIdx[col] = i
	}

	// Prepare new records
	var newRecords [][]string
	newRecords = append(newRecords, header)

	for _, row := range records[1:] {
		// Concatenate the fields
		input := row[colIdx["VendorID"]] +
			row[colIdx["lpep_pickup_datetime"]] +
			row[colIdx["lpep_dropoff_datetime"]] +
			row[colIdx["PULocationID"]] +
			row[colIdx["DOLocationID"]] +
			row[colIdx["fare_amount"]] +
			row[colIdx["trip_distance"]]

		hash := md5.Sum([]byte(input))
		hashStr := hex.EncodeToString(hash[:])

		newRow := append(row, hashStr)
		newRecords = append(newRecords, newRow)
	}

	// Write to the new file
	out, err := os.Create(outputFile)
	if err != nil {
		panic(err)
	}
	defer out.Close()

	w := csv.NewWriter(out)
	err = w.WriteAll(newRecords)
	if err != nil {
		panic(err)
	}

	fmt.Println("Output written to:", outputFile)
}
