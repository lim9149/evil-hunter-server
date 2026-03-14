// DEV-DIRECTION-LOCK: Portrait TownWorld UI / overlay panels / bottom fixed menu / visible hunt-return loop / original implementation only.
using System;
using System.Collections;
using System.Text;
using UnityEngine;
using UnityEngine.Networking;

namespace MurimInnRebuild
{
    public sealed class ServerApiClient : MonoBehaviour
    {
        public ApiConfig config;

        public IEnumerator GetJson(string path, Action<string> onSuccess, Action<string> onError)
        {
            yield return Send("GET", path, null, onSuccess, onError);
        }

        public IEnumerator PostJson(string path, string json, Action<string> onSuccess, Action<string> onError)
        {
            yield return Send("POST", path, json, onSuccess, onError);
        }

        private IEnumerator Send(string method, string path, string bodyJson, Action<string> onSuccess, Action<string> onError)
        {
            string baseUrl = config != null ? config.baseUrl.TrimEnd('/') : "http://127.0.0.1:8000";
            int retries = config != null ? Mathf.Max(0, config.maxRetryCount) : 1;
            float timeout = config != null ? Mathf.Max(3f, config.timeoutSec) : 10f;
            string url = baseUrl + path;

            for (int attempt = 0; attempt <= retries; attempt++)
            {
                using (UnityWebRequest req = new UnityWebRequest(url, method))
                {
                    req.downloadHandler = new DownloadHandlerBuffer();
                    req.timeout = Mathf.CeilToInt(timeout);
                    if (!string.IsNullOrEmpty(bodyJson))
                    {
                        byte[] bytes = Encoding.UTF8.GetBytes(bodyJson);
                        req.uploadHandler = new UploadHandlerRaw(bytes);
                        req.SetRequestHeader("Content-Type", "application/json");
                    }

                    yield return req.SendWebRequest();
                    bool ok = req.result == UnityWebRequest.Result.Success && req.responseCode >= 200 && req.responseCode < 300;
                    if (ok)
                    {
                        onSuccess?.Invoke(req.downloadHandler.text);
                        yield break;
                    }

                    if (attempt >= retries)
                    {
                        onError?.Invoke($"{req.responseCode} {req.error}
{req.downloadHandler.text}");
                        yield break;
                    }
                }

                yield return new WaitForSecondsRealtime(0.6f * (attempt + 1));
            }
        }
    }
}
