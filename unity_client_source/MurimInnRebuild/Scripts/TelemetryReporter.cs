// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace MurimInnRebuild
{
    public sealed class TelemetryReporter : MonoBehaviour
    {
        public ServerApiClient apiClient;
        public string accountId = "acc_demo";

        public void Report(string eventType, string eventName, string payloadJson = "{}")
        {
            TelemetryBatchDto batch = new TelemetryBatchDto
            {
                events = new List<TelemetryEventDto>
                {
                    new TelemetryEventDto
                    {
                        accountId = accountId,
                        eventType = eventType,
                        eventName = eventName,
                        payloadJson = payloadJson
                    }
                }
            };
            string body = JsonUtility.ToJson(batch);
            if (body.Contains("payloadJson"))
            {
                body = body.Replace("payloadJson", "payload");
            }
            StartCoroutine(apiClient.PostJson("/telemetry/events", body, _ => { }, Debug.LogWarning));
        }
    }
}
