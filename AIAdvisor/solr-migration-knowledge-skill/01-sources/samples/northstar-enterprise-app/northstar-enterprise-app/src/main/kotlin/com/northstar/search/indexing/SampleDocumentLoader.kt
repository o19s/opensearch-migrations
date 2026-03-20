package com.northstar.search.indexing

import com.fasterxml.jackson.core.type.TypeReference
import com.fasterxml.jackson.databind.ObjectMapper
import com.northstar.search.domain.AtlasDocument
import org.springframework.core.io.ClassPathResource
import org.springframework.stereotype.Component

@Component
class SampleDocumentLoader(
    private val objectMapper: ObjectMapper
) {
    fun load(): List<AtlasDocument> {
        val resource = ClassPathResource("samples/northstar-sample-docs.json")
        resource.inputStream.use { input ->
            return objectMapper.readValue(input, object : TypeReference<List<AtlasDocument>>() {})
        }
    }
}
