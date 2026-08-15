{{- define "monitor.name" -}}
monitor
{{- end }}

{{- define "monitor.fullname" -}}
{{ .Release.Name }}-monitor
{{- end }}

{{- define "monitor.labels" -}}
app.kubernetes.io/name: {{ include "monitor.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "monitor.selectorLabels" -}}
app.kubernetes.io/name: {{ include "monitor.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
