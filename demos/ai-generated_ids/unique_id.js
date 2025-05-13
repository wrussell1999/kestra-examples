const fs = require('fs');
const csv = require('csv-parser');
const fastCsv = require('fast-csv');
const crypto = require('crypto');

const inputFile = 'green_tripdata_2019-01.csv';
const outputFile = 'your_output_file_with_hashes.csv';

const results = [];

fs.createReadStream(inputFile)
  .pipe(csv())
  .on('data', (data) => {
    const inputStr = `${data.VendorID}${data.lpep_pickup_datetime}${data.lpep_dropoff_datetime}${data.PULocationID}${data.DOLocationID}${data.fare_amount}${data.trip_distance}`;
    const hash = crypto.createHash('md5').update(inputStr).digest('hex');
    data.unique_row_id = hash;
    results.push(data);
  })
  .on('end', () => {
    fastCsv
      .writeToPath(outputFile, results, { headers: true })
      .on('finish', () => {
        console.log(`File written to ${outputFile}`);
      });
  });
