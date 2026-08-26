package com.alfred.android.capabilities.shortcuts

import java.util.concurrent.ConcurrentHashMap

class WorkflowStore {
    private val workflows = ConcurrentHashMap<String, List<WorkflowStep>>()
    fun save(name: String, steps: List<WorkflowStep>) { workflows[name.lowercase()] = steps }
    fun get(name: String): List<WorkflowStep>? = workflows[name.lowercase()]
    fun delete(name: String) { workflows.remove(name.lowercase()) }
    fun all(): Map<String, List<WorkflowStep>> = workflows.toMap()
}
