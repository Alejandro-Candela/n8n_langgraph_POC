# Deploy WhatsApp → LangGraph workflow to n8n
# Usage: .\scripts\deploy_n8n_workflow.ps1

$API_KEY = $env:N8N_API_KEY
if (-not $API_KEY) {
    $API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJiMjRlOTZjMy1jMjU4LTRmODctOGZlYS0yYjA3N2NhZTA2ZGEiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiNjVjZjA2ZjgtYjQxZC00M2YzLWI5MjUtMTg0NzZiZDQ1ZWVjIiwiaWF0IjoxNzcxNTExMTI3fQ.oe_BRiwuh-rpH2ScKbSpBU_E1p8n1Mayp46MxuyyRy0"
}
$N8N_URL = "http://localhost:5678"
$WORKFLOW_ID = "wv71grwp4LT9W1nM"

$headers = @{
    "X-N8N-API-KEY" = $API_KEY
    "Content-Type" = "application/json"
}

$workflow = @{
    name = "WhatsApp LangGraph Synthesizer"
    nodes = @(
        # 1. Webhook - receives WhatsApp messages from Meta
        @{
            id = "webhook-1"
            name = "WhatsApp Webhook"
            type = "n8n-nodes-base.webhook"
            typeVersion = 2.1
            position = @(250, 300)
            webhookId = "3e9ef623-33a4-4536-a62c-14384508cc9a"
            parameters = @{
                path = "3e9ef623-33a4-4536-a62c-14384508cc9a"
                httpMethod = "={{$request.method}}"
                responseMode = "responseNode"
                options = @{}
            }
        }
        # 2. IF node - check if verification request (GET with hub.mode=subscribe)
        @{
            id = "if-verify"
            name = "Is Verification?"
            type = "n8n-nodes-base.if"
            typeVersion = 2
            position = @(480, 300)
            parameters = @{
                conditions = @{
                    options = @{
                        caseSensitive = $true
                        leftValue = ""
                        typeValidation = "strict"
                    }
                    conditions = @(
                        @{
                            id = "cond-1"
                            leftValue = '={{ $json.query["hub.mode"] }}'
                            rightValue = "subscribe"
                            operator = @{
                                type = "string"
                                operation = "equals"
                            }
                        }
                    )
                    combinator = "and"
                }
                options = @{}
            }
        }
        # 3. Respond Verification - returns hub.challenge for Meta verification
        @{
            id = "respond-verify"
            name = "Respond Verification"
            type = "n8n-nodes-base.respondToWebhook"
            typeVersion = 1.1
            position = @(730, 200)
            parameters = @{
                respondWith = "text"
                responseBody = '={{ $json.query["hub.challenge"] }}'
                options = @{
                    responseCode = 200
                }
            }
        }
        # 4. Extract Message - Code node to parse WhatsApp message payload
        @{
            id = "extract-msg"
            name = "Extract Message"
            type = "n8n-nodes-base.code"
            typeVersion = 2
            position = @(730, 400)
            parameters = @{
                jsCode = @"
// Extract WhatsApp message from Meta webhook payload
const body = $input.first().json.body;

// Safety check
if (!body || !body.entry || !body.entry[0]) {
  return [{ json: { skip: true, reason: 'No entry in payload' } }];
}

const entry = body.entry[0];
const changes = entry.changes;

if (!changes || !changes[0] || !changes[0].value) {
  return [{ json: { skip: true, reason: 'No changes in payload' } }];
}

const value = changes[0].value;

// Check for actual messages (not status updates)
if (!value.messages || !value.messages[0]) {
  return [{ json: { skip: true, reason: 'Status update, not a message' } }];
}

const message = value.messages[0];
const contact = value.contacts ? value.contacts[0] : {};

return [{
  json: {
    skip: false,
    messageId: message.id,
    from: message.from,
    timestamp: message.timestamp,
    type: message.type,
    text: message.type === 'text' ? message.text.body : `[${message.type} message]`,
    contactName: contact.profile ? contact.profile.name : 'Unknown',
    phoneNumberId: value.metadata ? value.metadata.phone_number_id : ''
  }
}];
"@
                mode = "runOnceForAllItems"
            }
        }
        # 5. Skip Check - IF node to skip status updates
        @{
            id = "if-skip"
            name = "Is Real Message?"
            type = "n8n-nodes-base.if"
            typeVersion = 2
            position = @(960, 400)
            parameters = @{
                conditions = @{
                    options = @{
                        caseSensitive = $true
                        leftValue = ""
                        typeValidation = "strict"
                    }
                    conditions = @(
                        @{
                            id = "cond-skip"
                            leftValue = "={{ $json.skip }}"
                            rightValue = $false
                            operator = @{
                                type = "boolean"
                                operation = "equals"
                            }
                        }
                    )
                    combinator = "and"
                }
                options = @{}
            }
        }
        # 6. Call LangGraph - HTTP Request to our service
        @{
            id = "call-langgraph"
            name = "Call LangGraph"
            type = "n8n-nodes-base.httpRequest"
            typeVersion = 4.2
            position = @(1190, 350)
            parameters = @{
                method = "POST"
                url = "http://poc-langgraph:8000/invoke"
                sendBody = $true
                specifyBody = "json"
                jsonBody = '={ "query": "{{ $json.text }}" }'
                options = @{
                    timeout = 60000
                }
            }
        }
        # 7. Format Response - Code node to build WhatsApp reply payload
        @{
            id = "format-response"
            name = "Format WhatsApp Reply"
            type = "n8n-nodes-base.code"
            typeVersion = 2
            position = @(1420, 350)
            parameters = @{
                jsCode = @"
// Get LangGraph response and original message data
const langgraphResponse = $input.first().json;
const extractedData = $('Extract Message').first().json;

// Build the response text
let responseText = '';

if (langgraphResponse.answer) {
  responseText = langgraphResponse.answer;
} else if (langgraphResponse.detail) {
  responseText = 'Lo siento, ocurrio un error procesando tu consulta. Intenta de nuevo.';
} else {
  responseText = JSON.stringify(langgraphResponse);
}

// Truncate to WhatsApp's 4096 char limit
if (responseText.length > 4000) {
  responseText = responseText.substring(0, 3997) + '...';
}

return [{
  json: {
    to: extractedData.from,
    phoneNumberId: extractedData.phoneNumberId,
    responseText: responseText,
    originalQuery: extractedData.text
  }
}];
"@
                mode = "runOnceForAllItems"
            }
        }
        # 8. Send WhatsApp Reply - HTTP Request to WhatsApp Cloud API
        @{
            id = "send-wa-reply"
            name = "Send WhatsApp Reply"
            type = "n8n-nodes-base.httpRequest"
            typeVersion = 4.2
            position = @(1650, 350)
            parameters = @{
                method = "POST"
                url = '=https://graph.facebook.com/v21.0/{{ $json.phoneNumberId }}/messages'
                sendHeaders = $true
                headerParameters = @{
                    parameters = @(
                        @{
                            name = "Authorization"
                            value = "Bearer {{ $env.WHATSAPP_ACCESS_TOKEN }}"
                        }
                    )
                }
                sendBody = $true
                specifyBody = "json"
                jsonBody = @"
{
  "messaging_product": "whatsapp",
  "to": "{{ $json.to }}",
  "type": "text",
  "text": {
    "body": "{{ $json.responseText }}"
  }
}
"@
                options = @{
                    timeout = 30000
                }
            }
        }
        # 9. Respond 200 OK - for the message webhook (Meta expects 200)
        @{
            id = "respond-ok"
            name = "Respond 200 OK"
            type = "n8n-nodes-base.respondToWebhook"
            typeVersion = 1.1
            position = @(1880, 350)
            parameters = @{
                respondWith = "noData"
                options = @{
                    responseCode = 200
                }
            }
        }
        # 10. Respond 200 for skipped messages (status updates)
        @{
            id = "respond-skip"
            name = "Respond Skip 200"
            type = "n8n-nodes-base.respondToWebhook"
            typeVersion = 1.1
            position = @(1190, 500)
            parameters = @{
                respondWith = "noData"
                options = @{
                    responseCode = 200
                }
            }
        }
    )
    connections = @{
        "WhatsApp Webhook" = @{
            main = @(
                ,@(
                    @{ node = "Is Verification?"; type = "main"; index = 0 }
                )
            )
        }
        "Is Verification?" = @{
            main = @(
                ,@(
                    @{ node = "Respond Verification"; type = "main"; index = 0 }
                )
                ,@(
                    @{ node = "Extract Message"; type = "main"; index = 0 }
                )
            )
        }
        "Extract Message" = @{
            main = @(
                ,@(
                    @{ node = "Is Real Message?"; type = "main"; index = 0 }
                )
            )
        }
        "Is Real Message?" = @{
            main = @(
                ,@(
                    @{ node = "Call LangGraph"; type = "main"; index = 0 }
                )
                ,@(
                    @{ node = "Respond Skip 200"; type = "main"; index = 0 }
                )
            )
        }
        "Call LangGraph" = @{
            main = @(
                ,@(
                    @{ node = "Format WhatsApp Reply"; type = "main"; index = 0 }
                )
            )
        }
        "Format WhatsApp Reply" = @{
            main = @(
                ,@(
                    @{ node = "Send WhatsApp Reply"; type = "main"; index = 0 }
                )
            )
        }
        "Send WhatsApp Reply" = @{
            main = @(
                ,@(
                    @{ node = "Respond 200 OK"; type = "main"; index = 0 }
                )
            )
        }
    }
    settings = @{
        executionOrder = "v1"
    }
} | ConvertTo-Json -Depth 15

Write-Host "Deploying workflow to n8n..."

try {
    $result = Invoke-RestMethod -Uri "$N8N_URL/api/v1/workflows/$WORKFLOW_ID" -Method Put -Headers $headers -Body $workflow
    Write-Host "SUCCESS: Workflow updated - ID: $($result.id), Name: $($result.name)"
    Write-Host "Nodes deployed: $($result.nodes.Count)"
    Write-Host "Active: $($result.active)"
} catch {
    Write-Host "ERROR: $($_.Exception.Message)"
    Write-Host "Response: $($_.ErrorDetails.Message)"
}
