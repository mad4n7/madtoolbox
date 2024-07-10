import java.io.FileWriter;
import java.io.IOException;
import java.util.*;

public class LanguageListSQLDump {
    public static void main(String[] args) {
        Map<String, String> languageMap = new TreeMap<>();
        
        for (String languageCode : Locale.getISOLanguages()) {
            Locale locale = new Locale(languageCode);
            String languageName = locale.getDisplayLanguage(Locale.ENGLISH);
            
            // Only add languages with non-empty names
            if (!languageName.isEmpty() && !languageName.equals(languageCode)) {
                // If the language is already in the map, prefer the shorter code
                if (!languageMap.containsKey(languageName) || languageCode.length() < languageMap.get(languageName).length()) {
                    languageMap.put(languageName, languageCode);
                }
            }
        }

        try (FileWriter writer = new FileWriter("languages.sql")) {
            writer.write("CREATE TABLE languages (\n");
            writer.write("    code VARCHAR(3) PRIMARY KEY,\n");
            writer.write("    name VARCHAR(100) NOT NULL\n");
            writer.write(");\n\n");
            writer.write("INSERT INTO languages (code, name) VALUES\n");
            
            List<String> insertStatements = new ArrayList<>();
            for (Map.Entry<String, String> entry : languageMap.entrySet()) {
                insertStatements.add(String.format("('%s', '%s')", entry.getValue(), entry.getKey().replace("'", "''")));
            }
            
            writer.write(String.join(",\n", insertStatements) + ";\n");
            
            System.out.println("SQL dump has been written to languages.sql");
        } catch (IOException e) {
            System.err.println("An error occurred while writing to the file: " + e.getMessage());
            e.printStackTrace();
        }
    }
}