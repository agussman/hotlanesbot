import { Component } from '@angular/core';
import { latLng, tileLayer } from 'leaflet';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Hot Lanes Bot';

  options = {
    layers: [
      tileLayer('http://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        detectRetina: true
      })
    ],
    zoom: 12,
    center: latLng([ 38.8427869, -77.2375653 ])
  };

}

@Component({
  selector: 'sidenav-drawer-overview-example',
  templateUrl: 'sidenav-drawer-overview-example.html',
  styleUrls: ['sidenav-drawer-overview-example.css'],
})
export class SidenavDrawerOverviewExample {}