using UnityEngine;

public static class JsonArrayHelper
{
    public static T[] FromJsonArray<T>(string json)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            return new T[0];
        }

        string trimmed = json.Trim();
        if (!trimmed.StartsWith("["))
        {
            Debug.LogWarning("JsonArrayHelper received non-array JSON. Returning empty array.");
            return new T[0];
        }

        string wrapped = "{\"items\":" + trimmed + "}";
        HunterArrayWrapper wrapper = JsonUtility.FromJson<HunterArrayWrapper>(wrapped);
        if (wrapper == null || wrapper.items == null)
        {
            return new T[0];
        }

        T[] result = new T[wrapper.items.Length];
        for (int i = 0; i < wrapper.items.Length; i++)
        {
            result[i] = (T)(object)wrapper.items[i];
        }

        return result;
    }
}
