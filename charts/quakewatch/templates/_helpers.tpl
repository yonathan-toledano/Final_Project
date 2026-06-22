{{- define "quakewatch.name" -}}
quakewatch
{{- end }}

{{- define "quakewatch.fullname" -}}
{{ .Release.Name }}-quakewatch
{{- end }}

{{- define "quakewatch.labels" -}}
app.kubernetes.io/name: {{ include "quakewatch.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "quakewatch.selectorLabels" -}}
app.kubernetes.io/name: {{ include "quakewatch.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
