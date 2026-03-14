using System;
using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public sealed class VillageSceneController : MonoBehaviour
{
    [Header("UI References")]
    [SerializeField] private TextMeshProUGUI accountInfoText;
    [SerializeField] private TMP_InputField hunterNameInput;
    [SerializeField] private TextMeshProUGUI createResultText;
    [SerializeField] private TextMeshProUGUI hunterListText;
    [SerializeField] private Button createHunterButton;
    [SerializeField] private Button listHuntersButton;

    private bool isBusy;

    private void Start()
    {
        RefreshAccountInfo();
        SetCreateMessage("준비 완료");
        SetHunterListMessage("헌터 목록을 불러오는 중...");
        StartCoroutine(ListHuntersRoutine());
    }

    public void OnCreateHunterButtonClicked()
    {
        if (!isBusy)
        {
            StartCoroutine(CreateHunterRoutine());
        }
    }

    public void OnListHuntersButtonClicked()
    {
        if (!isBusy)
        {
            StartCoroutine(ListHuntersRoutine());
        }
    }

    private void RefreshAccountInfo()
    {
        string serverUrl = SafeValue(SessionData.ServerUrl);
        string accountId = SafeValue(SessionData.AccountId);
        string deviceId = SafeValue(SessionData.DeviceId);

        if (accountInfoText != null)
        {
            accountInfoText.text =
                "AccountId: " + accountId + "\n" +
                "DeviceId: " + deviceId + "\n" +
                "Server: " + serverUrl;
        }
    }

    private IEnumerator CreateHunterRoutine()
    {
        string hunterName = hunterNameInput != null ? hunterNameInput.text.Trim() : string.Empty;
        if (string.IsNullOrEmpty(hunterName))
        {
            SetCreateMessage("헌터 이름을 입력하세요.");
            yield break;
        }

        string accountId = SafeValue(SessionData.AccountId);
        if (string.IsNullOrEmpty(accountId) || accountId == "-")
        {
            SetCreateMessage("AccountId가 비어 있습니다. 다시 로그인하세요.");
            yield break;
        }

        isBusy = true;
        SetButtonsInteractable(false);
        SetCreateMessage("빈 슬롯을 찾는 중...");

        HunterDto[] existingHunters = null;
        string listError = null;

        yield return StartCoroutine(SendGet(
            "/hunters?accountId=" + UnityWebRequest.EscapeURL(accountId),
            json => { existingHunters = JsonArrayHelper.FromJsonArray<HunterDto>(json); },
            error => { listError = error; }
        ));

        if (!string.IsNullOrEmpty(listError))
        {
            isBusy = false;
            SetButtonsInteractable(true);
            SetCreateMessage("목록 조회 실패: " + listError);
            yield break;
        }

        int nextSlot = FindNextAvailableSlot(existingHunters);
        CreateHunterRequest request = new CreateHunterRequest
        {
            hunterId = Guid.NewGuid().ToString("N"),
            accountId = accountId,
            slotIndex = nextSlot,
            name = hunterName
        };

        string requestJson = JsonUtility.ToJson(request);
        string createError = null;

        SetCreateMessage("헌터 생성 중...");

        yield return StartCoroutine(SendPost(
            "/hunters",
            requestJson,
            json => { SetCreateMessage("헌터 생성 성공! 슬롯 " + nextSlot); },
            error => { createError = error; }
        ));

        isBusy = false;
        SetButtonsInteractable(true);

        if (!string.IsNullOrEmpty(createError))
        {
            SetCreateMessage("헌터 생성 실패: " + createError);
            yield break;
        }

        if (hunterNameInput != null)
        {
            hunterNameInput.text = string.Empty;
        }

        yield return StartCoroutine(ListHuntersRoutine());
    }

    private IEnumerator ListHuntersRoutine()
    {
        string accountId = SafeValue(SessionData.AccountId);
        if (string.IsNullOrEmpty(accountId) || accountId == "-")
        {
            SetHunterListMessage("AccountId가 비어 있습니다. 다시 로그인하세요.");
            yield break;
        }

        isBusy = true;
        SetButtonsInteractable(false);
        SetHunterListMessage("헌터 목록을 불러오는 중...");

        HunterDto[] hunters = null;
        string listError = null;

        yield return StartCoroutine(SendGet(
            "/hunters?accountId=" + UnityWebRequest.EscapeURL(accountId),
            json => { hunters = JsonArrayHelper.FromJsonArray<HunterDto>(json); },
            error => { listError = error; }
        ));

        isBusy = false;
        SetButtonsInteractable(true);

        if (!string.IsNullOrEmpty(listError))
        {
            SetHunterListMessage("목록 조회 실패\n" + listError);
            yield break;
        }

        SetHunterListMessage(FormatHunterList(hunters));
    }

    private int FindNextAvailableSlot(HunterDto[] hunters)
    {
        for (int slot = 0; slot < 50; slot++)
        {
            bool used = false;
            if (hunters != null)
            {
                for (int i = 0; i < hunters.Length; i++)
                {
                    if (hunters[i] != null && hunters[i].slotIndex == slot)
                    {
                        used = true;
                        break;
                    }
                }
            }

            if (!used)
            {
                return slot;
            }
        }

        return 0;
    }

    private string FormatHunterList(HunterDto[] hunters)
    {
        if (hunters == null || hunters.Length == 0)
        {
            return "등록된 헌터가 없습니다.";
        }

        StringBuilder sb = new StringBuilder();
        sb.AppendLine("헌터 목록");

        for (int i = 0; i < hunters.Length; i++)
        {
            HunterDto hunter = hunters[i];
            if (hunter == null)
            {
                continue;
            }

            string displayName = string.IsNullOrEmpty(hunter.name) ? "(이름 없음)" : hunter.name;
            string jobId = string.IsNullOrEmpty(hunter.jobId) ? "novice" : hunter.jobId;
            string huntZone = string.IsNullOrEmpty(hunter.assignedHuntZoneId) ? "-" : hunter.assignedHuntZoneId;

            sb.AppendLine("--------------------");
            sb.AppendLine("슬롯: " + hunter.slotIndex);
            sb.AppendLine("이름: " + displayName);
            sb.AppendLine("직업: " + jobId);
            sb.AppendLine("레벨: " + hunter.level);
            sb.AppendLine("티어: " + SafeValue(hunter.tierId, "T1"));
            sb.AppendLine("AI 모드: " + SafeValue(hunter.aiMode, "autonomous"));
            sb.AppendLine("사냥터: " + huntZone);
        }

        return sb.ToString();
    }

    private IEnumerator SendGet(string path, Action<string> onSuccess, Action<string> onError)
    {
        string url = BuildUrl(path);
        using (UnityWebRequest request = UnityWebRequest.Get(url))
        {
            ApplyAuthorizationHeader(request);
            request.timeout = 10;
            yield return request.SendWebRequest();

            bool success = request.result == UnityWebRequest.Result.Success &&
                           request.responseCode >= 200 &&
                           request.responseCode < 300;

            if (success)
            {
                onSuccess?.Invoke(request.downloadHandler.text);
            }
            else
            {
                onError?.Invoke(BuildRequestError(request));
            }
        }
    }

    private IEnumerator SendPost(string path, string json, Action<string> onSuccess, Action<string> onError)
    {
        string url = BuildUrl(path);
        byte[] bodyRaw = Encoding.UTF8.GetBytes(json);

        using (UnityWebRequest request = new UnityWebRequest(url, "POST"))
        {
            request.uploadHandler = new UploadHandlerRaw(bodyRaw);
            request.downloadHandler = new DownloadHandlerBuffer();
            request.timeout = 10;
            request.SetRequestHeader("Content-Type", "application/json");
            ApplyAuthorizationHeader(request);
            yield return request.SendWebRequest();

            bool success = request.result == UnityWebRequest.Result.Success &&
                           request.responseCode >= 200 &&
                           request.responseCode < 300;

            if (success)
            {
                onSuccess?.Invoke(request.downloadHandler.text);
            }
            else
            {
                onError?.Invoke(BuildRequestError(request));
            }
        }
    }

    private void ApplyAuthorizationHeader(UnityWebRequest request)
    {
        string token = SafeValue(SessionData.AccessToken);
        if (!string.IsNullOrEmpty(token) && token != "-")
        {
            request.SetRequestHeader("Authorization", "Bearer " + token);
        }
    }

    private string BuildUrl(string path)
    {
        string serverUrl = SafeValue(SessionData.ServerUrl);
        serverUrl = serverUrl.TrimEnd('/');
        if (string.IsNullOrEmpty(serverUrl) || serverUrl == "-")
        {
            serverUrl = "http://127.0.0.1:8000";
        }

        if (!path.StartsWith("/"))
        {
            path = "/" + path;
        }

        return serverUrl + path;
    }

    private string BuildRequestError(UnityWebRequest request)
    {
        string body = request.downloadHandler != null ? request.downloadHandler.text : string.Empty;
        return request.responseCode + " " + request.error + "\n" + body;
    }

    private void SetButtonsInteractable(bool value)
    {
        if (createHunterButton != null) createHunterButton.interactable = value;
        if (listHuntersButton != null) listHuntersButton.interactable = value;
    }

    private void SetCreateMessage(string message)
    {
        if (createResultText != null) createResultText.text = message;
    }

    private void SetHunterListMessage(string message)
    {
        if (hunterListText != null) hunterListText.text = message;
    }

    private string SafeValue(string value, string fallback = "-")
    {
        return string.IsNullOrEmpty(value) ? fallback : value;
    }
}
