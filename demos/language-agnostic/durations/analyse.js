const fs = require('fs');
const path = require('path');

// Helper to parse ISO 8601 durations like "PT0.123S"
function parseISODuration(duration) {
    const regex = /PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+\.?\d*)S)?/;
    const matches = duration.match(regex);

    if (!matches) return 0;

    const hours = parseFloat(matches[1] || 0);
    const minutes = parseFloat(matches[2] || 0);
    const seconds = parseFloat(matches[3] || 0);

    return (hours * 3600) + (minutes * 60) + seconds;
}

// Load and parse the JSON file
const filePath = path.join(__dirname, 'make_data.json');
fs.readFile(filePath, 'utf8', (err, jsonData) => {
    if (err) {
        console.error('Error reading file:', err);
        return;
    }

    try {
        const data = JSON.parse(jsonData);
        const executions = data.results || [];

        let totalDuration = 0;
        let count = 0;

        executions.forEach(exec => {
            const tasks = exec.taskRunList || [];
            tasks.forEach(task => {
                if (task.taskId === 'python') {
                    const isoDuration = task?.state?.duration;
                    if (isoDuration) {
                        const seconds = parseISODuration(isoDuration);
                        totalDuration += seconds;
                        count++;
                    }
                }
            });
        });

        if (count > 0) {
            const avg = totalDuration / count;
            console.log(`Average duration for 'transform' task: ${avg.toFixed(3)} seconds`);
        } else {
            console.log("No 'transform' task durations found.");
        }

    } catch (parseErr) {
        console.error('Error parsing JSON:', parseErr);
    }
});
