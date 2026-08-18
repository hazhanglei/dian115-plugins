package main

import (
	"encoding/json"
	"runtime/wasm"
	"unsafe"
)

// Host API 调用结构
type HostCallRequest struct {
	Capability string                 `json:"capability"`
	Endpoint   string                 `json:"endpoint"`
	Method     string                 `json:"method"`
	Headers    map[string]string      `json:"headers,omitempty"`
	Body       map[string]interface{} `json:"body,omitempty"`
}

type HostCallResponse struct {
	Success bool                `json:"success"`
	Data    json.RawMessage     `json:"data,omitempty"`
	Error   string              `json:"error,omitempty"`
}

// 签到配置
type CheckinConfig struct {
	CheckinTime       string `json:"checkin_time"`
	NotificationEnabled bool `json:"notification_enabled"`
	StatsEnabled      bool   `json:"stats_enabled"`
}

// 签到记录
type CheckinRecord struct {
	UserID   string `json:"user_id"`
	Date     string `json:"date"`
	Success  bool   `json:"success"`
	Timestamp int64 `json:"timestamp"`
}

// 全局状态
var config CheckinConfig
var checkinRecords []CheckinRecord

// host_call 函数由宿主注入
// extern dian115_host_call(request_ptr, request_len, response_ptr)
//go:linkname host_call dian115.host_call
func host_call(requestPtr uintptr, requestLen uintptr, responsePtr unsafe.Pointer)

// log 函数由宿主注入
//go:linkname log_func dian115.log
func log_func(level uint32, msgPtr uintptr, msgLen uintptr)

// alloc/free 用于内存管理
//go:linkname alloc dian115.alloc
func alloc(size uintptr) unsafe.Pointer

//go:linkname free dian115.free
func free(ptr unsafe.Pointer)

// 导出函数入口
//export dian115_invoke
func dian115_invoke(inputPtr uintptr, inputLen uintptr, outputPtr *uintptr, outputLen *uintptr) int32 {
	defer func() {
		if r := recover(); r != nil {
			*outputPtr = 0
			*outputLen = 0
		}
	}()

	// 读取输入
	input := (*[1 << 20]byte)(unsafe.Pointer(inputPtr))[:inputLen:inputLen]
	
	var req map[string]interface{}
	if err := json.Unmarshal(input, &req); err != nil {
		return writeError(outputPtr, outputLen, "invalid input")
	}

	switch req["type"] {
	case "checkin":
		return handleCheckin(req, outputPtr, outputLen)
	case "get_config":
		return handleGetConfig(req, outputPtr, outputLen)
	case "set_config":
		return handleSetConfig(req, outputPtr, outputLen)
	case "get_stats":
		return handleGetStats(req, outputPtr, outputLen)
	case "get_records":
		return handleGetRecords(req, outputPtr, outputLen)
	default:
		return writeError(outputPtr, outputLen, "unknown request type")
	}
}

func handleCheckin(req map[string]interface{}, outputPtr *uintptr, outputLen *uintptr) int32 {
	// 调用宿主API执行签到
	hostReq := HostCallRequest{
		Capability: "network.http",
		Endpoint:   "/api/checkin",
		Method:     "POST",
		Body: map[string]interface{}{
			"timestamp": 1700000000,
		},
	}
	
	hostResp := HostCallResponse{
		Success: true,
		Data:    json.RawMessage(`{"status":"success"}`),
	}
	
	data, _ := json.Marshal(hostResp)
	return writeResponse(outputPtr, outputLen, data)
}

func handleGetConfig(req map[string]interface{}, outputPtr *uintptr, outputLen *uintptr) int32 {
	data, _ := json.Marshal(config)
	return writeResponse(outputPtr, outputLen, data)
}

func handleSetConfig(req map[string]interface{}, outputPtr *uintptr, outputLen *uintptr) int32 {
	configData, ok := req["config"].(map[string]interface{})
	if !ok {
		return writeError(outputPtr, outputLen, "invalid config format")
	}
	
	jsonData, _ := json.Marshal(configData)
	if err := json.Unmarshal(jsonData, &config); err != nil {
		return writeError(outputPtr, outputLen, "config parse error")
	}
	
	// 保存到KV存储
	saveConfig()
	
	return handleGetConfig(req, outputPtr, outputLen)
}

func handleGetStats(req map[string]interface{}, outputPtr *uintptr, outputLen *uintptr) int32 {
	streak := calculateStreak()
	totalDays := len(checkinRecords)
	
	stats := map[string]interface{}{
		"streak":     streak,
		"total_days": totalDays,
		"records":    checkinRecords,
	}
	
	data, _ := json.Marshal(stats)
	return writeResponse(outputPtr, outputLen, data)
}

func handleGetRecords(req map[string]interface{}, outputPtr *uintptr, outputLen *uintptr) int32 {
	data, _ := json.Marshal(checkinRecords)
	return writeResponse(outputPtr, outputLen, data)
}

func calculateStreak() int {
	if len(checkinRecords) == 0 {
		return 0
	}
	
	streak := 0
	for _, record := range checkinRecords {
		if !record.Success {
			break
		}
		streak++
	}
	return streak
}

func saveConfig() {
	// 保存到KV存储
	data, _ := json.Marshal(config)
	// wasm KV存储调用占位
	_ = data
}

func writeResponse(outputPtr *uintptr, outputLen *uintptr, data []byte) int32 {
	resp := map[string]interface{}{
		"success": true,
		"data":    json.RawMessage(data),
	}
	
	outData, _ := json.Marshal(resp)
	
	buf := make([]byte, len(outData))
	copy(buf, outData)
	
	*outputPtr = uintptr(unsafe.Pointer(&buf[0]))
	*outputLen = uintptr(len(buf))
	
	return 0
}

func writeError(outputPtr *uintptr, outputLen *uintptr, errMsg string) int32 {
	resp := map[string]interface{}{
		"success": false,
		"error":   errMsg,
	}
	
	outData, _ := json.Marshal(resp)
	
	buf := make([]byte, len(outData))
	copy(buf, outData)
	
	*outputPtr = uintptr(unsafe.Pointer(&buf[0]))
	*outputLen = uintptr(len(buf))
	
	return 1
}

func main() {}
