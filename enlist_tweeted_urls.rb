#! /usr/bin/env ruby

require 'csv'
require 'uri'
require 'pry'
require 'mechanize'

def get_status_ids(file)
  status_ids = Array.new

  csvDatas = CSV.read(file, col_sep: ",", headers: false)
  csvDatas.each do  |row|
    status_ids << row[0]
  end
  return status_ids
end

def get_tweeted_urls(status_ids)
  urls = Array.new
  agent = Mechanize.new
  tweeted_urls = Array.new

  status_ids.each do |url|
    begin
      page = agent.get("https://twitter.com/datasci_blogs/status/#{url}")
    rescue Timeout::Error
      next
    rescue WWW::Mechanize::ResponseCodeError => e
      case e.responce_code
      when "404"
        next
      when "502"
        retry
      else
        puts "cahght Exception : #{e.response_code}"
        retry
      end
    end
    tweeted_urls = URI.extract(page.title, ["http", "https"])
    tweeted_urls.each do |str|
      str.gsub!(/(http.+\.+$)/, "")  # eliminate like "http://..."
      urls << [url, str]
    end
  end
  return urls
end


# main
file = ARGV[0]
status_ids = get_status_ids(file)
get_tweeted_urls(status_ids).each do |raw|
  puts "#{raw[0]}, #{raw[1]}"
end
