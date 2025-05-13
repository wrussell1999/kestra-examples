package main

import (
    "encoding/csv"
    "fmt"
    "os"
    "strconv"
)

func main() {
    dataset := os.Getenv("DATASET")
    discountStr := os.Getenv("DISCOUNTED_AMOUNT")
    outFile := os.Getenv("FILENAME")

    discount, _ := strconv.ParseFloat(discountStr, 64)

    f, _ := os.Open(dataset)
    r := csv.NewReader(f)
    header, _ := r.Read()

    totalIdx := -1
    for i, h := range header {
        if h == "total" {
            totalIdx = i
            break
        }
    }

    var out [][]string
    var sum float64
    if discount > 0 {
        header = append(header, "discounted_total")
    }
    out = append(out, header)

    for {
        row, err := r.Read()
        if err != nil {
            break
        }
        val, _ := strconv.ParseFloat(row[totalIdx], 64)
        sum += val
        if discount > 0 {
            disc := val * (1 - discount)
            row = append(row, fmt.Sprintf("%.2f", disc))
        }
        out = append(out, row)
    }

    output := fmt.Sprintf("::{\"total\": \"Hello\"}::", sum)
    fmt.Println(output)

    if discount > 0 {
        w, err := os.Create(outFile)
        if err != nil {
            panic(fmt.Errorf("failed to create file: %w", err))
        }
        defer w.Close()

        writer := csv.NewWriter(w)
        err = writer.WriteAll(out)
        if err != nil {
            panic(fmt.Errorf("error writing CSV: %w", err))
        }
    }
}
